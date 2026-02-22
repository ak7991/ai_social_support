# ai_social_support
An AI-powered system that can parse documents intelligently and provide actionable insights to citizens.


# Product Design

## User Journey
A User can login using their username, password. They can upload a host of 
documents on the dashboard. Before uploading any document, they need to 
create a "profile" of the user they are uploading for, i.e. they need to tell 
name, age, gender, etc of the person they are uploading these documents for. 
While uploading the documents the user must also tell which document is what, so 
they should first select a document from the dropdown and then attach the relevant 
file.  
There ideally should be two buttons at the end of upload, one to "validate" uploaded 
documents, and the second to submit the documents. The validations should happen 
instantly, and the validations should be basic validation, for eg:
- are the documents in the correct format (pdf/jpeg/png)?
- did the user upload the correct documents?


For now the form and its fields will be in English, but soon we should support 
Arabic as the primary language.

## Admin Journey
An Admin can login using their username, password. They can see profiles of users 
who have uploaded their documents. The profiles where the AI is still processing 
will be shown as "in-process", otherwise it will show "done". The "done" profiles 
would also show if the AI determined the profile as:
- accepted: profiles that should receive financial support
- declined: profiles that shouldn't receive financial support
The admin has to manually review the declined profiles and verify if AI's assessment 
is correct or not.



# Solution Design
Documents that users can upload can be roughly classified in two categories:
- documents with limited formats (like identity cards, credit reports, etc)
- documents with too many formats (like bank statements, resume, etc)


For handwritten forms, we might suffer from accuracy issues if an LLM does the OCR 
for us, so instead we should employ a custom OCR solution like Google Vision and 
analyse the data on the OCR text.
