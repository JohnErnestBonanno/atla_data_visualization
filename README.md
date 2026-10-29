Avatar the Last Airbender

Pound for pound, Avatar the Last Airbender (ATLA) is the greatest show ever made.

This data project will be broken up into 2 parts:
1. Pulling and enriching data from the [Avatar Wiki](https://avatar.fandom.com/wiki/Avatar_Wiki) through Beautiful Soup. High level steps include:
    * Pulling each episode transcript (via BeautifulSoup) 
    * Count the number of words each charcter says (Pandas)
    * Add each character's ethnicity (i.e Water Tribe) based on the Wiki
2. Creatively visualize the final output

Tech Used:
- BeautifulSoup
- Requests
- PATH

Use of AI:
* Claude assisted in the creation of the pulling/enriching python files. In particular, AI was helpful with:
    * setting up proper request structure with the Avatar Wiki
    * cleaning text via Regular Expressions and removing stage instructions
    * scaling a single episode to the entire series

Findings:
- TBD

Future Work:
- I could create a manual mapping file for charcters that don't have an ethnicity according to the wiki. For example, despite being obvisouly Fire Nation, neither "Young Azula" nor "Young Zuko" are listed as such. From there, specific judgment calls would have to be made. I'd argue that Appa ic clearly an Air Nomad, but I'm not sure Momo would follow that definition. Do we assume the actress that plays Katara in Book 3's "The Ember Island Players" is Fire Nation? That being said, I don't think it changes the final data visualizations.

Upskill Lessons
* Proper folder design
    * I focused on using an src structure with extract, transform, and viz to improve reproducability. 
    * Additionaly, creating a seperate folder for exploratory notebooks kept my work much cleaner.
* UV instead of pip
    * Historically, I've always used pip to install packages in python, but for this project I experimented with uv which is both faster and can handle virtual environments
* Use PATH's pathlib
    * In using a proper folder structure with src, I needed a more robust way to navigate folders. Pathlib allowed me to move in and out of src's data folders
* CoCoding w/ AI
    * I personally find it better to ask AI for help on individual parts of code, rather than trying to "one-shot" the entire ask, otherwise, in my opinion, too much of the code gets abstracted away and troubleshooting becomes diffucult. However, I think it is worth it to trade speed for understanding.  


