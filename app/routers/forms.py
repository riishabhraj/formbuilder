from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Form, User, Submission
from ..schemas import form as schemas
from ..schemas import submission as submission_schemas
from ..utils.auth import require_user, get_current_user
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forms", tags=["forms"])

@router.post("/create", response_model=schemas.FormResponse)
async def create_form(
    form_data: schemas.FormCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    try:
        # Convert fields to JSON string for storage
        fields_json = json.dumps([field.dict() for field in form_data.fields])
        
        db_form = Form(
            title=form_data.title,
            description=form_data.description,
            fields=fields_json,
            creator_id=current_user.id
        )
        
        db.add(db_form)
        db.commit()
        db.refresh(db_form)
        
        # Convert stored JSON string back to list for response
        form_dict = {
            "id": db_form.id,
            "title": db_form.title,
            "description": db_form.description,
            "fields": json.loads(db_form.fields),
            "creator_id": db_form.creator_id
        }
        
        return schemas.FormResponse(
            status="success",
            data=schemas.Form(**form_dict)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=List[schemas.FormResponse])
async def get_all_forms(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    try:
        forms = db.query(Form).filter(Form.creator_id == current_user.id).all()
        
        # Convert each form to the correct response format
        return [
            schemas.FormResponse(
                status="success",
                data=schemas.Form(
                    id=form.id,
                    title=form.title,
                    description=form.description,
                    fields=json.loads(form.fields) if isinstance(form.fields, str) else form.fields,
                    creator_id=form.creator_id
                )
            )
            for form in forms
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{form_id}", response_model=schemas.FormResponse)
async def get_form(
    form_id: int,
    db: Session = Depends(get_db)
):
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Convert stored JSON string back to list
    fields = json.loads(form.fields) if isinstance(form.fields, str) else form.fields
    
    # Create form dict with parsed fields
    form_dict = {
        "id": form.id,
        "title": form.title,
        "description": form.description,
        "fields": fields,
        "creator_id": form.creator_id
    }
    
    # Return in the correct format
    return schemas.FormResponse(
        status="success",
        data=schemas.Form(**form_dict)
    )

@router.delete("/delete/{form_id}")
async def delete_form(
    form_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Attempting to delete form {form_id} by user {current_user.id}")
        
        # First get the form without any filters
        form = db.query(Form).filter(Form.id == form_id).first()
        
        logger.info(f"Form query result: {form}")
        
        if not form:
            logger.error(f"Form {form_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Form with ID {form_id} not found"
            )
            
        logger.info(f"Form creator_id: {form.creator_id}, Current user id: {current_user.id}")
        
        # Check if user owns the form
        if form.creator_id != current_user.id:
            logger.error(f"User {current_user.id} not authorized to delete form {form_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this form"
            )
        
        # Delete associated submissions first
        db.query(Submission).filter(Submission.form_id == form_id).delete()
        
        # Then delete the form
        db.delete(form)
        db.commit()
        
        logger.info(f"Successfully deleted form {form_id}")
        
        return {
            "status": "success",
            "message": f"Form {form_id} deleted successfully"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting form: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/submit/{form_id}/", response_model=submission_schemas.SubmissionResponse)
async def submit_form(
    form_id: int,
    submission: submission_schemas.SubmissionCreate,
    db: Session = Depends(get_db)
):
    try:
        # Check if form exists
        form = db.query(Form).filter(Form.id == form_id).first()
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        # Convert submission to dict for storage
        submission_data = {resp.field_id: resp.value for resp in submission.responses}
        
        # Create new submission
        db_submission = Submission(
            form_id=form_id,
            data=submission_data  # Store the data directly
        )
        
        db.add(db_submission)
        db.commit()
        db.refresh(db_submission)
        
        # Return the complete submission data
        return submission_schemas.SubmissionResponse(
            status="success",
            message="Form submitted successfully",
            submission_id=db_submission.id,
            data=db_submission.data,  # Include the submitted data
            submitted_at=db_submission.submitted_at  # Include the timestamp
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/submissions/{form_id}", response_model=List[submission_schemas.SubmissionResponse])
async def get_form_submissions(
    form_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    try:
        # Check if form exists and belongs to user
        form = db.query(Form).filter(
            Form.id == form_id,
            Form.creator_id == current_user.id
        ).first()
        
        if not form:
            raise HTTPException(
                status_code=404,
                detail="Form not found or you don't have access to it"
            )

        # Calculate offset for pagination
        offset = (page - 1) * limit

        # Get submissions with pagination
        submissions = db.query(Submission)\
            .filter(Submission.form_id == form_id)\
            .offset(offset)\
            .limit(limit)\
            .all()

        # Format response
        return [
            submission_schemas.SubmissionResponse(
                status="success",
                message="Submission retrieved successfully",
                submission_id=sub.id,
                data=sub.data,
                submitted_at=sub.submitted_at
            )
            for sub in submissions
        ]

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )

@router.get("/submissions", response_model=List[submission_schemas.SubmissionResponse])
async def get_all_submissions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    try:
        # Calculate offset for pagination
        offset = (page - 1) * limit

        # Get all submissions for forms owned by the user
        submissions = db.query(Submission)\
            .join(Form)\
            .filter(Form.creator_id == current_user.id)\
            .offset(offset)\
            .limit(limit)\
            .all()

        # Format response
        return [
            submission_schemas.SubmissionResponse(
                status="success",
                message="Submission retrieved successfully",
                submission_id=sub.id,
                data=sub.data,
                submitted_at=sub.submitted_at
            )
            for sub in submissions
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        ) 