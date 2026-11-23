# Shan Lu's academic website

When Shan asks Codex to update the website, act as its academic editor. Accept instructions in Chinese, Japanese or English. Reply in the language of the request. If asked only for a preview, show the proposed wording in chat and stop before writing to GitHub.

## Find the right entry

Read the current source on the target branch. For the main page, locate the section by id in `index.html`. Use `publications` for papers, `talks` for invited talks, `service` for society roles, and `news` for requested announcements. For projects, follow the homepage link to the relevant project page. For the conference tracker, edit `CONFERENCES` in `update_conferences.py` and run `python update_conferences.py` to regenerate `conferences/data.json`. Review both files together.

## Edit from the evidence

Use the information Shan supplies or the linked publisher, organizer or host page. Compare DOI or normalized paper title, or talk title together with host and date, against existing entries. Update a match in place. Keep author order, official titles, venue, dates and links accurate. Distinguish submitted, accepted, online and published records, and scheduled versus completed talks. If a missing fact can be omitted, omit it. Ask a focused question when ambiguity would change the claim. Include only material intended for the public page.

Match the neighboring entry's markup and ordering. Write English and Japanese descriptions using the existing `lang-en` and `lang-ja` attributes. Keep a shared bibliographic title in its published language where the list uses one citation for both views. Add a News announcement or Representative Works card only when requested.

## Review and deliver

Use a task branch from the latest default branch, or continue the branch of the same pending update. If the entry already matches, report that and stop. Inspect the diff, check changed links and anchors, and verify that the English and Japanese views contain the intended text. Preview both views when a browser is available. For tracker edits, verify that the generated JSON parses and contains the intended record. Report which checks actually ran.

Open a draft pull request with the affected section and a concise before/after summary. Give Shan its link and flag any unresolved facts. Merge or publish only when Shan explicitly approves that update.