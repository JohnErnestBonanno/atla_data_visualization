Avatar the Last Airbender

Pound for pound, Avatar the Last Airbender (ATLA) is the greatest show ever made.

This data project will explore pulling and visualzing who ATLA transcripts. 

To Do:
* Update transcript_pull to stop pulling data:
    * when we hit "fade to black" OR 
    * when we move to the Cast Header... 

* Add Notebook folder for EDA and troubleshooting
* Create git branches for different parts of work


Tech Used:
- BeautifulSoup
- Requests
- PATH

Use of AI:
* Claude assisted in the creation of the transcript_to_df python function. In particular, AI was helpful with:
    * setting up the request structure
    * cleaning text via Regular Expressions

Findings:
- TBD

Future Work:
- TBD

Upskill Lessons
* Proper folder design
    * I focused on using an src structure with extract, transform, and viz to improve reproducability
* UV instead of pip
    * Historically, I've always used pip to install packages in python, but for this project I experimented with uv which is both faster and can handle virtual environments
* Use PATH's pathlib
    * In using a proper folder structure with src, I needed a more robust way to navigate folders. Pathlib allowed me to move in and out of src's data folders



