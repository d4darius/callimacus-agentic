"""Paragraph evaluation dataset with ground truth classifications."""

document = {}


#Dataset examples
content_input_1 = {
    "audio_transcription": "Let's talk about Storage Limitation, it's a principle that requires that personal data must not be maintained for longer than is necessary. For Example, suppose that an agent starts an action after eight years, nine years from the determination of the agreement, the employer do not have the optimal evidence, it's a proof for demonstrating, demonstrating for instance, that he acted in a lawful way, because he stored data for a period of time, not sufficient to the evidence, this is the foreman most trading, it's lawful, it's lawful behavior",
    "documentation": "Storage Limitation\nThe storage limitation principle requires that personal data must not be maintained for longer than is necessary to fulfil the goal of their collection. Data must be erased when the data processing purpose is achieved. This means that storing any data longer than necessary is not permitted (art. 5.1.e).",
    "student_notes": "### Storage Limitation: personal data must not be maintained for longer that is necessary",
    "current_paragraph": {
        "audio_transcription": "",
        "documentation": "",
        "student_notes": ""
    },
    "document_thread": """
---------- Full document ----------

"""
}

content_input_2 = {
    "audio_transcription": "The banks, banks are obliged to store documents of their clients for ten years, they are obliged. This is not in my case, yes, in my case, as lawyers I am also obliged, but in, for instance, for the example, the relationship, employment relationship between employer and employee does not exist this obligation",
    "documentation": "Storage Limitation\nThe storage limitation principle requires that personal data must not be maintained for longer than is necessary to fulfil the goal of their collection. Data must be erased when the data processing purpose is achieved. This means that storing any data longer than necessary is not permitted (art. 5.1.e).",
    "student_notes": "### Storage Limitation: personal data must not be maintained for longer that is necessary, obligations for banks",
    "current_paragraph": {
        "audio_transcription": "Let's talk about Storage Limitation, it's a principle that requires that personal data must not be maintained for longer than is necessary. For Example, suppose that an agent starts an action after eight years, nine years from the determination of the agreement, the employer do not have the optimal evidence, it's a proof for demonstrating, demonstrating for instance, that he acted in a lawful way, because he stored data for a period of time, not sufficient to the evidence, this is the foreman most trading, it's lawful, it's lawful behavior",
        "documentation": "# Storage Limitation\nThe storage limitation principle requires that personal data must not be maintained for longer than is necessary to fulfil the goal of their collection. Data must be erased when the data processing purpose is achieved. This means that storing any data longer than necessary is not permitted (art. 5.1.e).",
        "student_notes": "### Storage Limitation: personal data must not be maintained for longer that is necessary"
    },
    "document_thread": """
---------- Full document ----------
"""
}

content_input_3 = {
    "audio_transcription": """For instance, if I have data regarding the fact that, I don't know, for instance, on that day, employee went home at six o'clock, at six o'clock, at two o'clock
 Maybe I can delete the data, but I'm not so sure that I can delete the data
 Because for instance, he had an accident at four o'clock, and if I deleted the fact that at two o'clock he went home, how can I demonstrate that he was not working in that moment and he left the office? So maybe with relation to employment relationship, I have to store all the data
 If I paid the loans, the time, working time, what else is easy, I have to store everything, because there could be so many situations connected to employment relationship in connection to which the employees can start action against the employer
 And therefore it is advisable to store all the data connected to the employment relationship""",
   "documentation": "Storage Limitation\nThe storage limitation principle requires that personal data must not be maintained for longer than is necessary to fulfil the goal of their collection. Data must be erased when the data processing purpose is achieved. This means that storing any data longer than necessary is not permitted (art. 5.1.e).",
    "student_notes": "### Storage Limitation: personal data must not be maintained for longer that is necessary, obligations for banks, not possible to store data on a period longer than x years",
    "current_paragraph": {
        "audio_transcription": "Let's talk about Storage Limitation, it's a principle that requires that personal data must not be maintained for longer than is necessary. For Example, suppose that an agent starts an action after eight years, nine years from the determination of the agreement, the employer do not have the optimal evidence, it's a proof for demonstrating, demonstrating for instance, that he acted in a lawful way, because he stored data for a period of time, not sufficient to the evidence, this is the foreman most trading, it's lawful, it's lawful behavior.\nThe banks, banks are obliged to store documents of their clients for ten years, they are obliged. This is not in my case, yes, in my case, as lawyers I am also obliged, but in, for instance, for the example, the relationship, employment relationship between employer and employee does not exist this obligation.",
        "documentation": "# Storage Limitation\nThe storage limitation principle requires that personal data must not be maintained for longer than is necessary to fulfil the goal of their collection. Data must be erased when the data processing purpose is achieved. This means that storing any data longer than necessary is not permitted (art. 5.1.e).",
        "student_notes": "### Storage Limitation: personal data must not be maintained for longer that is necessary, obligations for banks"
    },
    "document_thread": """
---------- Full document ----------
"""
}

content_input_4 = {
    "audio_transcription": """
Principles of integrity and confidentiality
 The principle of integrity is provided by article 5
1
S, which says that personal data should be processed in a manner that ensures appropriate security of the personal data, including protection against auto-allorized or unlawful processing or against accidental loss, destruction or damage using appropriate technical and professional measures
 These are the principle of integrity and confidentiality
 What is this with that? Also, loss of data is infringement, it's a violation
""",
"documentation": "Integrity and confidentiality\nProtection of personal data against unauthorized or unlawful processing, accidental loss, destruction or damage is at the core of the principle of integrity and confidentiality (art. 5.1.f).\nEnsure that personal data is not available to everyone within an organisation, but only to those who actually have to work with the data.\nThe intensity of security measures is directly linked to the potential risk of data processing operations (risk-based approach).",
"student_notes": "### Integrity and confidentiality: loss or destruction of data is a violation of this principle,",
"current_paragraph": {
        "audio_transcription": "Let's talk about Storage Limitation, it's a principle that requires that personal data must not be maintained for longer than is necessary. For Example, suppose that an agent starts an action after eight years, nine years from the determination of the agreement, the employer do not have the optimal evidence, it's a proof for demonstrating, demonstrating for instance, that he acted in a lawful way, because he stored data for a period of time, not sufficient to the evidence, this is the foreman most trading, it's lawful, it's lawful behavior.\nThe banks, banks are obliged to store documents of their clients for ten years, they are obliged. This is not in my case, yes, in my case, as lawyers I am also obliged, but in, for instance, for the example, the relationship, employment relationship between employer and employee does not exist this obligation.\nFor instance, if I have data regarding the fact that, I don't know, for instance, on that day, employee went home at six o'clock, at six o'clock, at two o'clock\nMaybe I can delete the data, but I'm not so sure that I can delete the data\nBecause for instance, he had an accident at four o'clock, and if I deleted the fact that at two o'clock he went home, how can I demonstrate that he was not working in that moment and he left the office? So maybe with relation to employment relationship, I have to store all the data\nIf I paid the loans, the time, working time, what else is easy, I have to store everything, because there could be so many situations connected to employment relationship in connection to which the employees can start action against the employer\nAnd therefore it is advisable to store all the data connected to the employment relationship",
        "documentation": "# Storage Limitation\nThe storage limitation principle requires that personal data must not be maintained for longer than is necessary to fulfil the goal of their collection. Data must be erased when the data processing purpose is achieved. This means that storing any data longer than necessary is not permitted (art. 5.1.e).",
        "student_notes": "### Storage Limitation: personal data must not be maintained for longer that is necessary, obligations for banks,  not possible to store data on a period longer than x years"
    },
"document_thread": """
---------- Full document ----------
"""
}

content_input_5 = {
    "audio_transcription": """
If the data controller or its data processor, the new data, in this case, loss, destruction and so on, is a violation of this principle
 And therefore the controller can be fined, because in this case, the destruction of data is a problem for the data controller
 In this case, the legislation pretends that the controller ensures that personal data is not available to everyone within an organization, but only to the person who needs to work with the data
 If I store personal data of any client, for instance, or a hospital, store personal data of persons in a place which are easily accessible to everyone of positions of violation, because of course, all the other places, for instance, I remember the tribunal of Florence, I had an hearing in the tribunal of Florence, and all the papers, all the filing of all the proceedings who are on the floor in the open, everyone can take files on certain hearings
 Of course, the person which circulates in the tribunal of Florence are loss processor, and loss processor, of course, are not controller, and can access this information
 This is a violation, it's not possible
 The filing of those reads the contrains to the person of data, the person of data, and you cannot leave on the floor in cases which are accessible to everyone
 And therefore, this is an infringement, it's strange that an infringement is made by a tribunal, but in any case, this is an infringement
 I cannot leave in my office files of my clients everywhere
 I have my room, they are stored, not only because of the files, I have, for instance, information on actually two inventions to be related, but also because in the files there are personal data, and I have to make sure that nobody can access to this personal data
 Of course, the protection in appliance of the principles of integrity and confidentiality requires the so-called risk-based approach that Professor Mantelli already explained to you
 What is the intensity, the strength of the measures applied is linked to the potential risk of the operation
""",
"documentation": "Integrity and confidentiality\nProtection of personal data against unauthorized or unlawful processing, accidental loss, destruction or damage is at the core of the principle of integrity and confidentiality (art. 5.1.f).\nEnsure that personal data is not available to everyone within an organisation, but only to those who actually have to work with the data.\nThe intensity of security measures is directly linked to the potential risk of data processing operations (risk-based approach).",
"student_notes": "### Integrity and confidentiality: loss or destruction of data is a violation of this principle, only the person needing the data has access to it",
"current_paragraph": {
        "audio_transcription": "Principles of integrity and confidentiality\n The principle of integrity is provided by article 51S,\n which says that personal data should be processed in a manner that ensures appropriate security of the personal data, including protection against auto-allorized or unlawful processing or against accidental loss, destruction or damage using appropriate technical and professional measures\n These are the principle of integrity and confidentiality\n What is this with that? Also, loss of data is infringement, it's a violation",
        "documentation": "Integrity and confidentiality\nProtection of personal data against unauthorized or unlawful processing, accidental loss, destruction or damage is at the core of the principle of integrity and confidentiality (art. 5.1.f).\nEnsure that personal data is not available to everyone within an organisation, but only to those who actually have to work with the data.\nThe intensity of security measures is directly linked to the potential risk of data processing operations (risk-based approach).",
        "student_notes": "### Integrity and confidentiality: loss or destruction of data is a violation of this principle,"
    },
"document_thread": """
---------- Full document ----------
### Storage Limitation
The `storage limitation` principle states that personal data must not be maintained for longer than is necessary to fulfill the purpose for which it was collected. Once the purpose of data processing has been achieved, the data must be erased. Storing data beyond what is necessary is not permitted, as established by Article 5.1.e of the relevant regulation.

- **Banks** are specifically obliged to store client documents for ten years, reflecting sector-specific legal requirements.
- In other contexts, such as the employment relationship between employer and employee, there is generally no such explicit obligation unless otherwise specified by law.
- Failing to retain data for the required period may result in insufficient evidence for lawful actions, while retaining data longer than necessary is also unlawful.

> For example, if an employer is required to demonstrate lawful behavior but has not stored data for a sufficient period, they may lack the necessary evidence. Conversely, banks are legally required to retain documents for a set period, illustrating how obligations can differ by sector.

**Key Point:** Personal data retention must always be justified by a specific, lawful purpose, and both under- and over-retention can have legal consequences.
"""
}

content_input_6 = {
    "audio_transcription": """
And then we have the principle of accountability
 I know that Professor Mantelli already explained to you the principle of accountability
 Do you want the principle of accountability in this? Okay
 And do you think that a person has been able to pass the people what they have done are he's compliant with them? Okay, and what do you think? Is there any list of measures that you have to adopt in order to be compliant with the GDPR or what? The GDPR says what you have to do in order to be compliant or not
 How do you prove to me that, how do you prove that you have been compliant? How do you prove that you have adopted a behavior in compliance with the GDPR? I think it's true that the government says you are a person who is not compliant with the GDPR
 Example, example
 This is the principle of accountability which is regulated by Article 5
2
""",
"documentation": "Accountability\nThe principle of accountability anticipates two obligations: an obligation to ensure compliance and the ability to prove it (art. 5.2).\nAll the necessary technical and organisational measures should be adopted and evidence thereof should be kept.",
"student_notes": "###Accountability",
"current_paragraph": {
        "audio_transcription": "Principles of integrity and confidentiality\n The principle of integrity is provided by article 51S,\n which says that personal data should be processed in a manner that ensures appropriate security of the personal data, including protection against auto-allorized or unlawful processing or against accidental loss, destruction or damage using appropriate technical and professional measures\nThese are the principle of integrity and confidentiality\n What is this with that? Also, loss of data is infringement, it's a violation\n If the data controller or its data processor, the new data, in this case, loss, destruction and so on, is a violation of this principle\nAnd therefore the controller can be fined, because in this case, the destruction of data is a problem for the data controller\nIn this case, the legislation pretends that the controller ensures that personal data is not available to everyone within an organization, but only to the person who needs to work with the data\nIf I store personal data of any client, for instance, or a hospital, store personal data of persons in a place which are easily accessible to everyone of positions of violation, because of course, all the other places, for instance, I remember the tribunal of Florence, I had an hearing in the tribunal of Florence, and all the papers, all the filing of all the proceedings who are on the floor in the open, everyone can take files on certain hearings\nOf course, the person which circulates in the tribunal of Florence are loss processor, and loss processor, of course, are not controller, and can access this information\nThis is a violation, it's not possible\nThe filing of those reads the contrains to the person of data, the person of data, and you cannot leave on the floor in cases which are accessible to everyone\nAnd therefore, this is an infringement, it's strange that an infringement is made by a tribunal, but in any case, this is an infringement\nI cannot leave in my office files of my clients everywhere\nI have my room, they are stored, not only because of the files, I have, for instance, information on actually two inventions to be related, but also because in the files there are personal data, and I have to make sure that nobody can access to this personal data\nOf course, the protection in appliance of the principles of integrity and confidentiality requires the so-called risk-based approach that Professor Mantelli already explained to you\nWhat is the intensity, the strength of the measures applied is linked to the potential risk of the operation",
        "documentation": "Integrity and confidentiality\nProtection of personal data against unauthorized or unlawful processing, accidental loss, destruction or damage is at the core of the principle of integrity and confidentiality (art. 5.1.f).\nEnsure that personal data is not available to everyone within an organisation, but only to those who actually have to work with the data.\nThe intensity of security measures is directly linked to the potential risk of data processing operations (risk-based approach).",
        "student_notes": "### Integrity and confidentiality: loss or destruction of data is a violation of this principle, only the person needing the data has access to it"
    },
"document_thread": """
---------- Full document ----------
### Storage Limitation
The `storage limitation` principle states that personal data must not be maintained for longer than is necessary to fulfill the purpose for which it was collected. Once the purpose of data processing has been achieved, the data must be erased. Storing data beyond what is necessary is not permitted, as established by Article 5.1.e of the relevant regulation.

- **Banks** are specifically obliged to store client documents for ten years, reflecting sector-specific legal requirements.
- In other contexts, such as the employment relationship between employer and employee, there is generally no such explicit obligation unless otherwise specified by law.
- Failing to retain data for the required period may result in insufficient evidence for lawful actions, while retaining data longer than necessary is also unlawful.

> For example, if an employer is required to demonstrate lawful behavior but has not stored data for a sufficient period, they may lack the necessary evidence. Conversely, banks are legally required to retain documents for a set period, illustrating how obligations can differ by sector.

**Key Point:** Personal data retention must always be justified by a specific, lawful purpose, and both under- and over-retention can have legal consequences.
"""
}

content_input_7 = {
    "audio_transcription": """
The controller should be responsible for and be able to demonstrate compliance with Article 1 with all the principles we have studied together and this is the principle of accountability
 Of course, these rights of the data subject the data subject remains in control of personal data
 In this case, what we have seen together is that we have to charge the rights to connect to the data subject which are the principles which must be at the base of the process of personal data
""",
"documentation": "Accountability\nThe principle of accountability anticipates two obligations: an obligation to ensure compliance and the ability to prove it (art. 5.2).\nAll the necessary technical and organisational measures should be adopted and evidence thereof should be kept.",
"student_notes": "###Accountability",
"current_paragraph": {
        "audio_transcription": "And then we have the principle of accountability\nI know that Professor Mantelli already explained to you the principle of accountability\nDo you want the principle of accountability in this? Okay\nAnd do you think that a person has been able to pass the people what they have done are he's compliant with them? Okay, and what do you think? Is there any list of measures that you have to adopt in order to be compliant with the GDPR or what? The GDPR says what you have to do in order to be compliant or not\nHow do you prove to me that, how do you prove that you have been compliant? How do you prove that you have adopted a behavior in compliance with the GDPR? I think it's true that the government says you are a person who is not compliant with the GDPR\nExample, example\nThis is the principle of accountability which is regulated by Article 5",
        "documentation": "Accountability\nThe principle of accountability anticipates two obligations: an obligation to ensure compliance and the ability to prove it (art. 5.2).\nAll the necessary technical and organisational measures should be adopted and evidence thereof should be kept.",
        "student_notes": "### Accountability"
    },
"document_thread": """
---------- Full document ----------
### Storage Limitation
The `storage limitation` principle states that personal data must not be maintained for longer than is necessary to fulfill the purpose for which it was collected. Once the purpose of data processing has been achieved, the data must be erased. Storing data beyond what is necessary is not permitted, as established by Article 5.1.e of the relevant regulation.

- **Banks** are specifically obliged to store client documents for ten years, reflecting sector-specific legal requirements.
- In other contexts, such as the employment relationship between employer and employee, there is generally no such explicit obligation unless otherwise specified by law.
- Failing to retain data for the required period may result in insufficient evidence for lawful actions, while retaining data longer than necessary is also unlawful.

> For example, if an employer is required to demonstrate lawful behavior but has not stored data for a sufficient period, they may lack the necessary evidence. Conversely, banks are legally required to retain documents for a set period, illustrating how obligations can differ by sector.

**Key Point:** Personal data retention must always be justified by a specific, lawful purpose, and both under- and over-retention can have legal consequences.

### Integrity and Confidentiality

The principles of `integrity and confidentiality` ensure that personal data, once collected, is properly protected against unauthorized access or misuse — both from **external threats** and **internal mismanagement**.

- Access should be limited only to **authorized personnel**.
- Risks include employees changing roles within a company but retaining access permissions from prior roles.
    - Cybersecurity policies must enforce **access rights revocation** upon internal transfers.
    - Breaches often stem from **internal flaws**, not just external attacks.

> 💡 **Example**: An HR employee moving to marketing but retaining full HR data access poses a major compliance risk.
>
"""
}

content_input_8 = {
    "audio_transcription": """
This means that data subject has a specific rights
 Do you know which are the rights belonging to the data subject? We have examined the principles constituting the base of the treatment of the processing of personal data
 This means that the data subject even has a specific rights
""",
"documentation": "Data Subject Rights\nThe subjects whose data is being processed remain in control of their own personal data. Therefore, it is necessary:\nto inform them about processing of their data, what data are processed, on which legal basis, etc.;\nand, upon their request:\n-correct their data\n-entirely or partly stop using their data\n-delete their data and “forget” them \n-provide them with a machine-readable copy of their data, to allow them to use it with another service provider.\nRequests submitted orally and in writing.\nArt. 12.",
"student_notes": "## Data subject’s rights:",
"current_paragraph": {
        "audio_transcription": "And then we have the principle of accountability\nI know that Professor Mantelli already explained to you the principle of accountability\nDo you want the principle of accountability in this? Okay\nAnd do you think that a person has been able to pass the people what they have done are he's compliant with them? Okay, and what do you think? Is there any list of measures that you have to adopt in order to be compliant with the GDPR or what? The GDPR says what you have to do in order to be compliant or not\nHow do you prove to me that, how do you prove that you have been compliant? How do you prove that you have adopted a behavior in compliance with the GDPR? I think it's true that the government says you are a person who is not compliant with the GDPR\nExample, example\nThis is the principle of accountability which is regulated by Article 5\nThe controller should be responsible for and be able to demonstrate compliance with Article 1 with all the principles we have studied together and this is the principle of accountability\nOf course, these rights of the data subject the data subject remains in control of personal data\nIn this case, what we have seen together is that we have to charge the rights to connect to the data subject which are the principles which must be at the base of the process of personal data",
        "documentation": "Accountability\nThe principle of accountability anticipates two obligations: an obligation to ensure compliance and the ability to prove it (art. 5.2).\nAll the necessary technical and organisational measures should be adopted and evidence thereof should be kept.",
        "student_notes": "### Accountability"
    },
"document_thread": """
---------- Full document ----------
### Storage Limitation
The `storage limitation` principle states that personal data must not be maintained for longer than is necessary to fulfill the purpose for which it was collected. Once the purpose of data processing has been achieved, the data must be erased. Storing data beyond what is necessary is not permitted, as established by Article 5.1.e of the relevant regulation.

- **Banks** are specifically obliged to store client documents for ten years, reflecting sector-specific legal requirements.
- In other contexts, such as the employment relationship between employer and employee, there is generally no such explicit obligation unless otherwise specified by law.
- Failing to retain data for the required period may result in insufficient evidence for lawful actions, while retaining data longer than necessary is also unlawful.

> For example, if an employer is required to demonstrate lawful behavior but has not stored data for a sufficient period, they may lack the necessary evidence. Conversely, banks are legally required to retain documents for a set period, illustrating how obligations can differ by sector.

**Key Point:** Personal data retention must always be justified by a specific, lawful purpose, and both under- and over-retention can have legal consequences.

### Integrity and Confidentiality

The principles of `integrity and confidentiality` ensure that personal data, once collected, is properly protected against unauthorized access or misuse — both from **external threats** and **internal mismanagement**.

- Access should be limited only to **authorized personnel**.
- Risks include employees changing roles within a company but retaining access permissions from prior roles.
    - Cybersecurity policies must enforce **access rights revocation** upon internal transfers.
    - Breaches often stem from **internal flaws**, not just external attacks.

> 💡 **Example**: An HR employee moving to marketing but retaining full HR data access poses a major compliance risk.
>
"""
}

content_input_9 = {
    "audio_transcription": """
In this slide, we see which are the rights subject has the right to be informed about the processing of this data what data is processed on which legal basis it's on
 Upon request, the data subject has the right to ask for the correction of his data
 The data subject has the right to request that data controller stops to use personal data
 The data subject has the right to be forgotten
 What means that data subject has the right to be forgotten? The data subject has the right to ask for the addition of personal data
 And then the data subject has the right to add a copy
""",
"documentation": "Data Subject Rights\nINFORMATION\nACCESS\nRECTIFICATION\nERASURE\nRESTRICTION OF PROCESSING\nDATA PORTABILITY\nOBJECTION\nNOT TO BE SUBJECT TO A DECISION BASED SOLELY ON AUTOMATED PROCESSING\n",
"student_notes": "## Data subject’s rights: correct their data, stop using their data (not necessarily forget it), delete their data, provide them a machine-readable copy of their data, these requests are submitted orally and in writing",
"current_paragraph": {
        "audio_transcription": "This means that data subject has a specific rights\n Do you know which are the rights belonging to the data subject? We have examined the principles constituting the base of the treatment of the processing of personal data\n This means that the data subject even has a specific rights",
        "documentation": "Data Subject Rights\nThe subjects whose data is being processed remain in control of their own personal data. Therefore, it is necessary:\nto inform them about processing of their data, what data are processed, on which legal basis, etc.;\nand, upon their request:\n-correct their data\n-entirely or partly stop using their data\n-delete their data and “forget” them \n-provide them with a machine-readable copy of their data, to allow them to use it with another service provider.\nRequests submitted orally and in writing.\nArt. 12.",
        "student_notes": "## Data subject’s rights:"
    },
"document_thread": """
---------- Full document ----------
### Storage Limitation
The `storage limitation` principle states that personal data must not be maintained for longer than is necessary to fulfill the purpose for which it was collected. Once the purpose of data processing has been achieved, the data must be erased. Storing data beyond what is necessary is not permitted, as established by Article 5.1.e of the relevant regulation.

- **Banks** are specifically obliged to store client documents for ten years, reflecting sector-specific legal requirements.
- In other contexts, such as the employment relationship between employer and employee, there is generally no such explicit obligation unless otherwise specified by law.
- Failing to retain data for the required period may result in insufficient evidence for lawful actions, while retaining data longer than necessary is also unlawful.

> For example, if an employer is required to demonstrate lawful behavior but has not stored data for a sufficient period, they may lack the necessary evidence. Conversely, banks are legally required to retain documents for a set period, illustrating how obligations can differ by sector.

**Key Point:** Personal data retention must always be justified by a specific, lawful purpose, and both under- and over-retention can have legal consequences.

### Integrity and Confidentiality

The principles of `integrity and confidentiality` ensure that personal data, once collected, is properly protected against unauthorized access or misuse — both from **external threats** and **internal mismanagement**.

- Access should be limited only to **authorized personnel**.
- Risks include employees changing roles within a company but retaining access permissions from prior roles.
    - Cybersecurity policies must enforce **access rights revocation** upon internal transfers.
    - Breaches often stem from **internal flaws**, not just external attacks.

> 💡 **Example**: An HR employee moving to marketing but retaining full HR data access poses a major compliance risk.
>

### Accountability

The `accountability` principle, introduced by the GDPR, shifts focus from punishment to **proactive evidence of compliance**.

- Different from `responsibility`, which only applies after a violation.
- Under accountability, organizations must be able to **prove at any time** that data protection principles have been followed.
- Requires **documentation, logs, and traceable decision-making processes**.

It promotes transparency and standardization in internal data handling procedures.

- Makes compliance an **ongoing effort**, not a one-time audit.

| Pros | Cons |
| --- | --- |
| Encourages proactive compliance | Requires detailed internal documentation |
| Reduces post-violation legal burden | Adds overhead to design and implementation stages |
| Strengthens user trust | Potentially resource-intensive for small companies |

> 💡 **Example**: Simply saying “the team decided it” is not sufficient — you must document the **risk assessment rationale** and design decisions.
>
"""
}

content_input_10 = {
    "audio_transcription": """
    Oh thank you, yes I think they don't hear from home but the microphone is picking up everything. I have had this problem multiple times with this room
    Thank you.
""",
"documentation": "Data Subject Rights\nINFORMATION\nACCESS\nRECTIFICATION\nERASURE\nRESTRICTION OF PROCESSING\nDATA PORTABILITY\nOBJECTION\nNOT TO BE SUBJECT TO A DECISION BASED SOLELY ON AUTOMATED PROCESSING\n",
"student_notes": "## Data subject’s rights: correct their data, stop using their data (not necessarily forget it), delete their data, provide them a machine-readable copy of their data, these requests are submitted orally and in writing",
"current_paragraph": {
        "audio_transcription": "This means that data subject has a specific rights  nDo you know which are the rights belonging to the data subject? We have examined the principles constituting the base of the treatment of the processing of personal data\nThis means that the data subject even has a specific rights\n In this slide, we see which are the rights subject has the right to be informed about the processing of this data what data is processed on which legal basis it's on\nUpon request, the data subject has the right to ask for the correction of his data\nThe data subject has the right to request that data controller stops to use personal data\nThe data subject has the right to be forgotten\nWhat means that data subject has the right to be forgotten? The data subject has the right to ask for the addition of personal data\n And then the data subject has the right to add a copy\n",
        "documentation": "Data Subject Rights\nThe subjects whose data is being processed remain in control of their own personal data. Therefore, it is necessary:\nto inform them about processing of their data, what data are processed, on which legal basis, etc.;\nand, upon their request:\n-correct their data\n-entirely or partly stop using their data\n-delete their data and “forget” them \n-provide them with a machine-readable copy of their data, to allow them to use it with another service provider.\nRequests submitted orally and in writing.\nArt. 12.",
        "student_notes": "## Data subject’s rights: correct their data, stop using their data (not necessarily forget it), delete their data, provide them a machine-readable copy of their data, these requests are submitted orally and in writing"
    },
"document_thread": """
---------- Full document ----------
### Storage Limitation
The `storage limitation` principle states that personal data must not be maintained for longer than is necessary to fulfill the purpose for which it was collected. Once the purpose of data processing has been achieved, the data must be erased. Storing data beyond what is necessary is not permitted, as established by Article 5.1.e of the relevant regulation.

- **Banks** are specifically obliged to store client documents for ten years, reflecting sector-specific legal requirements.
- In other contexts, such as the employment relationship between employer and employee, there is generally no such explicit obligation unless otherwise specified by law.
- Failing to retain data for the required period may result in insufficient evidence for lawful actions, while retaining data longer than necessary is also unlawful.

> For example, if an employer is required to demonstrate lawful behavior but has not stored data for a sufficient period, they may lack the necessary evidence. Conversely, banks are legally required to retain documents for a set period, illustrating how obligations can differ by sector.

**Key Point:** Personal data retention must always be justified by a specific, lawful purpose, and both under- and over-retention can have legal consequences.

### Integrity and Confidentiality

The principles of `integrity and confidentiality` ensure that personal data, once collected, is properly protected against unauthorized access or misuse — both from **external threats** and **internal mismanagement**.

- Access should be limited only to **authorized personnel**.
- Risks include employees changing roles within a company but retaining access permissions from prior roles.
    - Cybersecurity policies must enforce **access rights revocation** upon internal transfers.
    - Breaches often stem from **internal flaws**, not just external attacks.

> 💡 **Example**: An HR employee moving to marketing but retaining full HR data access poses a major compliance risk.
>

### Accountability

The `accountability` principle, introduced by the GDPR, shifts focus from punishment to **proactive evidence of compliance**.

- Different from `responsibility`, which only applies after a violation.
- Under accountability, organizations must be able to **prove at any time** that data protection principles have been followed.
- Requires **documentation, logs, and traceable decision-making processes**.

It promotes transparency and standardization in internal data handling procedures.

- Makes compliance an **ongoing effort**, not a one-time audit.

| Pros | Cons |
| --- | --- |
| Encourages proactive compliance | Requires detailed internal documentation |
| Reduces post-violation legal burden | Adds overhead to design and implementation stages |
| Strengthens user trust | Potentially resource-intensive for small companies |

> 💡 **Example**: Simply saying “the team decided it” is not sufficient — you must document the **risk assessment rationale** and design decisions.
>
"""
}

content_input_11 = {
    "audio_transcription": """
Which are these rights belonging to the data subject
 Here we have the list of the rights pertaining to the data subject
 The right of information, right of access, right of recognition, a region, restriction of processing, the data of ability, objection, and right to be subject to a decision based solely on automatic processing
""",
"documentation": "Data Subject Rights\nINFORMATION\nACCESS\nRECTIFICATION\nERASURE\nRESTRICTION OF PROCESSING\nDATA PORTABILITY\nOBJECTION\nNOT TO BE SUBJECT TO A DECISION BASED SOLELY ON AUTOMATED PROCESSING\n",
"student_notes": "## Data subject’s rights: correct their data, stop using their data (not necessarily forget it), delete their data, provide them a machine-readable copy of their data, these requests are submitted orally and in writing",
"current_paragraph": {
        "audio_transcription": "This means that data subject has a specific rights\nDo you know which are the rights belonging to the data subject? We have examined the principles constituting the base of the treatment of the processing of personal data\nThis means that the data subject even has a specific rights\nIn this slide, we see which are the rights subject has the right to be informed about the processing of this data what data is processed on which legal basis it's on\nUpon request, the data subject has the right to ask for the correction of his data\nThe data subject has the right to request that data controller stops to use personal data\nThe data subject has the right to be forgotten\nWhat means that data subject has the right to be forgotten? The data subject has the right to ask for the addition of personal data\nAnd then the data subject has the right to add a copy",
        "documentation": "Data Subject Rights\nThe subjects whose data is being processed remain in control of their own personal data. Therefore, it is necessary:\nto inform them about processing of their data, what data are processed, on which legal basis, etc.;\nand, upon their request:\n-correct their data\n-entirely or partly stop using their data\n-delete their data and “forget” them \n-provide them with a machine-readable copy of their data, to allow them to use it with another service provider.\nRequests submitted orally and in writing.\nArt. 12.",
        "student_notes": "## Data subject’s rights: correct their data, stop using their data (not necessarily forget it), delete their data, provide them a machine-readable copy of their data, these requests are submitted orally and in writing"
    },
"document_thread": """
---------- Full document ----------
### Storage Limitation
The `storage limitation` principle states that personal data must not be maintained for longer than is necessary to fulfill the purpose for which it was collected. Once the purpose of data processing has been achieved, the data must be erased. Storing data beyond what is necessary is not permitted, as established by Article 5.1.e of the relevant regulation.

- **Banks** are specifically obliged to store client documents for ten years, reflecting sector-specific legal requirements.
- In other contexts, such as the employment relationship between employer and employee, there is generally no such explicit obligation unless otherwise specified by law.
- Failing to retain data for the required period may result in insufficient evidence for lawful actions, while retaining data longer than necessary is also unlawful.

> For example, if an employer is required to demonstrate lawful behavior but has not stored data for a sufficient period, they may lack the necessary evidence. Conversely, banks are legally required to retain documents for a set period, illustrating how obligations can differ by sector.

**Key Point:** Personal data retention must always be justified by a specific, lawful purpose, and both under- and over-retention can have legal consequences.

### Integrity and Confidentiality

The principles of `integrity and confidentiality` ensure that personal data, once collected, is properly protected against unauthorized access or misuse — both from **external threats** and **internal mismanagement**.

- Access should be limited only to **authorized personnel**.
- Risks include employees changing roles within a company but retaining access permissions from prior roles.
    - Cybersecurity policies must enforce **access rights revocation** upon internal transfers.
    - Breaches often stem from **internal flaws**, not just external attacks.

> 💡 **Example**: An HR employee moving to marketing but retaining full HR data access poses a major compliance risk.
>

### Accountability

The `accountability` principle, introduced by the GDPR, shifts focus from punishment to **proactive evidence of compliance**.

- Different from `responsibility`, which only applies after a violation.
- Under accountability, organizations must be able to **prove at any time** that data protection principles have been followed.
- Requires **documentation, logs, and traceable decision-making processes**.

It promotes transparency and standardization in internal data handling procedures.

- Makes compliance an **ongoing effort**, not a one-time audit.

| Pros | Cons |
| --- | --- |
| Encourages proactive compliance | Requires detailed internal documentation |
| Reduces post-violation legal burden | Adds overhead to design and implementation stages |
| Strengthens user trust | Potentially resource-intensive for small companies |

> 💡 **Example**: Simply saying “the team decided it” is not sufficient — you must document the **risk assessment rationale** and design decisions.
>
"""
}

content_input_12 = {
    "audio_transcription": """
Let's start with the right to be informed
 With reference to the right to be informed, what is the right to be informed? In this sense, we already read the work of the web series, the data subject has the right to be informed about the fact that the subject, so we space the controller, is collected and using personal data
 This information, of course, shall be given at the moment in which the data is collected, or if the data is obtained by someone, someone else, at the latest one month after obtaining the data
 What is this principle? What is this principle? What is this right? What is the right to be informed? And you understand what is this right to be informed
 So that data must be collected
""",
"documentation": "Right to be informed\nData subjects must be informed about the collection and use of their personal data. This information should be communicated at the following moments:\nat the time of collection of their personal data from them;\nif data are obtained from someone else, at the latest one month after obtaining the data.\n\nThis information should mainly be provided via privacy policy of controller.\nThe information must be easily accessible and written in clear and simple language. To assess whether these conditions are fulfilled, it must be considered the target audience.",
"student_notes": "### Right to be informed: the data subject has the right to be informed that the data is being collected,",
"current_paragraph": {
        "audio_transcription": "This means that data subject has a specific rights\n Do you know which are the rights belonging to the data subject? We have examined the principles constituting the base of the treatment of the processing of personal data\nThis means that the data subject even has a specific rights\nIn this slide, we see which are the rights subject has the right to be informed about the processing of this data what data is processed on which legal basis it's o\n Upon request, the data subject has the right to ask for the correction of his data\nThe data subject has the right to request that data controller stops to use personal data\nThe data subject has the right to be forgotten\nWhat means that data subject has the right to be forgotten? The data subject has the right to ask for the addition of personal data\nAnd then the data subject has the right to add a copy\nWhich are these rights belonging to the data subject\n Here we have the list of the rights pertaining to the data subject\n The right of information, right of access, right of recognition, a region, restriction of processing, the data of ability, objection, and right to be subject to a decision based solely on automatic processing",
        "documentation": "Data Subject Rights\nThe subjects whose data is being processed remain in control of their own personal data. Therefore, it is necessary:\nto inform them about processing of their data, what data are processed, on which legal basis, etc.;\nand, upon their request:\n-correct their data\n-entirely or partly stop using their data\n-delete their data and “forget” them \n-provide them with a machine-readable copy of their data, to allow them to use it with another service provider.\nRequests submitted orally and in writing.\nArt. 12.",
        "student_notes": "## Data subject’s rights: correct their data, stop using their data (not necessarily forget it), delete their data, provide them a machine-readable copy of their data, these requests are submitted orally and in writing"
    },
"document_thread": """
---------- Full document ----------
### Storage Limitation
The `storage limitation` principle states that personal data must not be maintained for longer than is necessary to fulfill the purpose for which it was collected. Once the purpose of data processing has been achieved, the data must be erased. Storing data beyond what is necessary is not permitted, as established by Article 5.1.e of the relevant regulation.

- **Banks** are specifically obliged to store client documents for ten years, reflecting sector-specific legal requirements.
- In other contexts, such as the employment relationship between employer and employee, there is generally no such explicit obligation unless otherwise specified by law.
- Failing to retain data for the required period may result in insufficient evidence for lawful actions, while retaining data longer than necessary is also unlawful.

> For example, if an employer is required to demonstrate lawful behavior but has not stored data for a sufficient period, they may lack the necessary evidence. Conversely, banks are legally required to retain documents for a set period, illustrating how obligations can differ by sector.

**Key Point:** Personal data retention must always be justified by a specific, lawful purpose, and both under- and over-retention can have legal consequences.

### Integrity and Confidentiality

The principles of `integrity and confidentiality` ensure that personal data, once collected, is properly protected against unauthorized access or misuse — both from **external threats** and **internal mismanagement**.

- Access should be limited only to **authorized personnel**.
- Risks include employees changing roles within a company but retaining access permissions from prior roles.
    - Cybersecurity policies must enforce **access rights revocation** upon internal transfers.
    - Breaches often stem from **internal flaws**, not just external attacks.

> 💡 **Example**: An HR employee moving to marketing but retaining full HR data access poses a major compliance risk.
>

### Accountability

The `accountability` principle, introduced by the GDPR, shifts focus from punishment to **proactive evidence of compliance**.

- Different from `responsibility`, which only applies after a violation.
- Under accountability, organizations must be able to **prove at any time** that data protection principles have been followed.
- Requires **documentation, logs, and traceable decision-making processes**.

It promotes transparency and standardization in internal data handling procedures.

- Makes compliance an **ongoing effort**, not a one-time audit.

| Pros | Cons |
| --- | --- |
| Encourages proactive compliance | Requires detailed internal documentation |
| Reduces post-violation legal burden | Adds overhead to design and implementation stages |
| Strengthens user trust | Potentially resource-intensive for small companies |

> 💡 **Example**: Simply saying “the team decided it” is not sufficient — you must document the **risk assessment rationale** and design decisions.
>
"""
}

# Triage outputs: "continue", "ignore", "new"
triage_output_1 = "continue"
triage_output_2 = "continue"
triage_output_3 = "continue"
triage_output_4 = "new"
triage_output_5 = "continue"
triage_output_6 = "new"
triage_output_7 = "continue"
triage_output_8 = "new"
triage_output_9 = "continue"
triage_output_10 = "ignore"
triage_output_11 = "continue"
triage_output_12 = "new"

write_criteria_1 = """
• No writing action is needed
• Ensure we continue with the paragraph  
"""

write_criteria_2 = """
• No writing action is needed
• Ensure we continue with the paragraph
"""

write_criteria_3 = """
• No writing action is needed
• Ensure we continue with the paragraph
"""

write_criteria_4 = """
• Write a new paragraph about Storage Limitation in a complete and coincise way
"""

write_criteria_5 = """
• No writing action is needed
• Ensure we continue with the paragraph
"""

write_criteria_6 = """
• Write a new paragraph about Integrity and Confidentiality in a complete and concise way
"""

write_criteria_7 = """
• No writing action is needed
• Ensure we continue with the paragraph
"""

write_criteria_8 = """
• Write a new paragraph about Accountability in a complete and concise way
"""

write_criteria_9 = """ 
• No writing action is needed
• Ensure we continue with the paragraph
"""

write_criteria_10 = """
• No writing action is needed
• Ensure we ignore the current data
"""

write_criteria_11 = """
• No writing action is needed
• Ensure we continue with the paragraph
"""

write_criteria_12 = """
• Write a new paragraph about Data subject’s rights in a complete and concise way
"""

examples_triage = [
  {
      "inputs": {"content_input": content_input_1},
      "outputs": {"classification": triage_output_1},
  },
  {
      "inputs": {"content_input": content_input_2},
      "outputs": {"classification": triage_output_2},
  },
  {
      "inputs": {"content_input": content_input_3},
      "outputs": {"classification": triage_output_3},
  },
  {
      "inputs": {"content_input": content_input_4},
      "outputs": {"classification": triage_output_4},
  },
  {
      "inputs": {"content_input": content_input_5},
      "outputs": {"classification": triage_output_5},
  },
  {
      "inputs": {"content_input": content_input_6},
      "outputs": {"classification": triage_output_6},
  },
  {
      "inputs": {"content_input": content_input_7},
      "outputs": {"classification": triage_output_7},
  },
  {
      "inputs": {"content_input": content_input_8},
      "outputs": {"classification": triage_output_8},
  },
  {
      "inputs": {"content_input": content_input_9},
      "outputs": {"classification": triage_output_9},
  },
  {
      "inputs": {"content_input": content_input_10},
      "outputs": {"classification": triage_output_10},
  },
  {
      "inputs": {"content_input": content_input_11},
      "outputs": {"classification": triage_output_11},
  },
  {
      "inputs": {"content_input": content_input_12},
      "outputs": {"classification": triage_output_12},
  },
]

content_inputs = [content_input_1, content_input_2, content_input_3, content_input_4, content_input_5, content_input_6, content_input_7, content_input_8, content_input_9, content_input_10, content_input_11, content_input_12]

content_names = ["content_input_1", "content_input_2", "content_input_3", "content_input_4", "content_input_5", "content_input_6", "content_input_7", "content_input_8", "content_input_9", "content_input_10", "content_input_11", "content_input_12"]

write_criteria_list = [write_criteria_1, write_criteria_2, write_criteria_3, write_criteria_4, write_criteria_5, write_criteria_6, write_criteria_7, write_criteria_8, write_criteria_9, write_criteria_10, write_criteria_11, write_criteria_12]

triage_outputs_list = [triage_output_1, triage_output_2, triage_output_3, triage_output_4, triage_output_5, triage_output_6, triage_output_7, triage_output_8, triage_output_9, triage_output_10, triage_output_11, triage_output_12]

# Define expected tool calls for each content response based on analysis
#TODO: use also enhance_content
# Options: write_content, done
expected_tool_calls = [
    [],                                                 # content_input_1: start paragraph on Storage Limitation
    [],                                                 # content_input_2: continue talking about Storage Limitation
    [],                                                 # content_input_3: continue talking about Storage Limitation
    ["write_content", "done"],                          # content_input_4: Start new paragraph on Integrity and Confidentiality
    [],                                                 # content_input_5: continue talking about Integrity and Confidentiality
    ["write_content", "done"],                          # content_input_6: Start new paragraph about Accountability
    [],                                                 # content_input_7: continue talking about Accountability
    ["write_content", "done"],                          # content_input_8: Start new paragraph about Data subject's rights
    [],                                                 # content_input_9: continue talking about Data subject's rights
    [],                                                 # content_input_10: ignore the technician who entered the room
    [],                                                 # content_input_11: continue talking about Data subject's rights
    ["write_content", "done"],                          # content_input_12: Start new paragraph about The right to be informed
]
