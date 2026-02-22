# AI-powered Social Support Recommender
An AI-powered system that can parse documents intelligently and can decide whether  
the person is eligible for financial support or not.  
Users can upload documents like their:  
- resume
- bank statements
- emirates id card
- credit report
- assets/liabilities excel  

After assessment the users can also chat with a bot to know the reasons behind their  
rejection. Additionally the chat-bot can also recommend other ways to for being more  
financially successful catered to specific user profiles.  


# User Journey
A User can login using their username, password (or they can signup using a new email).  
They can upload a host of documents on the dashboard. Before uploading any document,  
they need to create a "profile" of the user they are uploading for, i.e. they need  
to tell name, age, gender, etc of the person they are uploading these documents for.  
While uploading the documents the user must also tell which document is what, so  
they should first select a document from the dropdown and then attach the relevant  
file.  

For now the form and its fields will be in English, but soon we should support 
Arabic as the primary language.
![user_journey](./ai_social_support_user_journey.png)


# Tech Spec
For the UI, we have portal with a couple of pages like:
- login/signup page  
- "home" page  
- create profile page  
The dashboard is build using Streamlit.
For the document processing backend, we have API's built on the FastAPI webserver.  
The actual extractions are done via multi-modal models hosted locally using Ollama.  
The results of the extractions are then stored in an RDBMS (postgres).  
We have a recommender which can take all the extractions as input and provide a  
recommendation whether the profile is eligible to get financial support or not.  
Finally there's another bot which the users can chat with regarding the decision.

# Future Roadmap 
Main aim should be to reduce production costs, while increasing accuracy.
## Document validations and preprocessing
We should ideally be doing 3 levels of preprocessing:  
- basic validations  
- custom validations
- image processing  

**Basic validations:**  
We should be checking size of documents uploaded, number of pages (in case of PDFs).

**Custom validations:**  
We should be checking if the user mistakenly submitted the wrong file, or if the  
file is in an unrecognised format, for eg: they submitted their driving licence  
in their id card, which don't support. This would help us in saving LLM inferences.  

**Image preprocessing:**
Most documents people scan are either unevenly lit, or tilted (or both). We need 
to fix as many inconsistencies as possible before we start parsing to improve accuracy  
of production systems.


## For document parsing
Documents that users can upload can be roughly classified in two categories:
- documents with limited formats (like identity cards, credit reports, etc)
- documents with too many formats (like bank statements, resume, etc)

**For documents with limited formats**, we should ideally be building custom rule  
based classifiers to reduce operational costs.
**For documents with no fixed formats** like bank statements, resumes, etc too we 
should ideally be looking at dedicated 3rd party services like Azure/GCP Document 
API's. They typically cost much less than an LLM's inference cost, and can provide 
better outputs, specially with encoded PDF's.
**If we support handwritten forms**, then we should definitely be using OCR services 
like Google vision, instead of relying on a multi-modal model or an in-house OCR 
model like Tesseract or something. The OCR's output can then be fed to a custom 
parser, since the formats are pretty limited.
