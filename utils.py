from fastapi.exceptions import HTTPException
from fastapi import status
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from starlette.responses import JSONResponse
from config import settings
from fastapi.templating import Jinja2Templates

def send_template_email(from_email, to_email, subject, template,**kwargs):
    email_templates = Jinja2Templates(directory="email_templates")
    template = email_templates.get_template(template)
    result =  send_email(from_email, to_email, subject, template.render(**kwargs))
    return result

def send_email(from_email, to_email, subject, content):
    message = Mail(
        from_email = from_email,
        to_emails = to_email,
        subject = subject,
        html_content= content
    )
    try:
        sg = SendGridAPIClient(settings.send_grid_key)
        sg.send(message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail= e)
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Email sent"})