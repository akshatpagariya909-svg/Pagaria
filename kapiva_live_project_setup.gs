/**
 * Kapiva Live Project – one-click setup.
 *
 * Run this ONCE while logged in as placement@xlri.ac.in:
 *   1. Go to https://script.google.com -> New project
 *   2. Paste this whole file, click Save, select `setup` and click Run
 *   3. Approve the permissions prompt (Forms + Gmail)
 *
 * What it does:
 *   - Creates the Google Form (Name, Roll Number, Project choice), restricted
 *     to signed-in XLRI accounts, one response per person, and roll numbers
 *     must look like an HRM 2025-27 roll number (H25xxx).
 *   - Copies the two JD PDFs from Richa Pathak's Kapiva email.
 *   - Puts the form link and both PDFs into the draft "Kapiva | Live Project | ..."
 *     that's already sitting in Drafts. Nothing is sent.
 */

const KAPIVA_MESSAGE_ID = '1a119e829a45415d';   // Richa Pathak's email (8 Oct, 10:36 AM)
const DRAFT_SUBJECT = 'Kapiva | Live Project | Deadline: 9th October 2026 23:59:59 HRS (IST)';
const PLACEHOLDER_URL = 'https://forms.gle/KAPIVA_FORM_LINK_PENDING';

const PROJECT_1 = "Decode How India's New-Age Consumer Brands Reward Their People";
const PROJECT_2 = "Decode How India's New-Age Consumer Brands Build Their Organisations";

function setup() {
  // ---- 1. Google Form ----
  const form = FormApp.create('Kapiva Live Project | Expression of Interest');
  form.setDescription(
    'For the HRM 2025-27 batch only.\n' +
    'Select ONE project. Deadline: 9th October 2026, 23:59:59 HRS (IST).'
  );
  form.setRequireLogin(true);            // only xlri.ac.in accounts can open it
  form.setCollectEmail(true);
  form.setLimitOneResponsePerUser(true);
  form.setAllowResponseEdits(true);

  form.addTextItem().setTitle('Name').setRequired(true);

  const rollValidation = FormApp.createTextValidation()
    .setHelpText('Enter your HRM 2025-27 roll number, e.g. H25049')
    .requireTextMatchesPattern('^[Hh]25\\d{3}$')
    .build();
  form.addTextItem()
    .setTitle('Roll Number')
    .setRequired(true)
    .setValidation(rollValidation);

  const choice = form.addMultipleChoiceItem();
  choice.setTitle('Which live project would you like to apply for? (select one)')
    .setChoices([choice.createChoice(PROJECT_1), choice.createChoice(PROJECT_2)])
    .setRequired(true);

  const formUrl = form.getPublishedUrl();
  let shortUrl = formUrl;
  try { shortUrl = form.shortenFormUrl(formUrl); } catch (e) { /* keep the long URL */ }

  // ---- 2. Attachments from Kapiva's email ----
  const attachments = GmailApp.getMessageById(KAPIVA_MESSAGE_ID).getAttachments();

  // ---- 3. Update the existing draft ----
  const draft = GmailApp.getDrafts().find(d => d.getMessage().getSubject() === DRAFT_SUBJECT);
  if (!draft) throw new Error('Draft not found: ' + DRAFT_SUBJECT);

  const msg = draft.getMessage();
  const html = msg.getBody()
    .split(PLACEHOLDER_URL).join(shortUrl)
    .replace(/<span style="background-color:\s*(#ffff00|rgb\(255,\s*255,\s*0\))">Link<\/span>/g, 'Link');
  const plain = msg.getPlainBody().split(PLACEHOLDER_URL).join(shortUrl);

  draft.update(msg.getTo(), DRAFT_SUBJECT, plain, {
    htmlBody: html,
    attachments: attachments,
  });

  Logger.log('Form (share this):  ' + shortUrl);
  Logger.log('Form (edit/responses): ' + form.getEditUrl());
  Logger.log('Attached: ' + attachments.map(a => a.getName()).join(', '));
  Logger.log('Draft updated. Review it in Gmail Drafts before sending.');
}
