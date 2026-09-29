# AILanguage

AILanguage is an optional Vale style for Red Hat technical documentation.
It identifies a small set of linguistic and structural patterns that commonly
occur in AI-assisted prose. It does not determine whether AI generated text.

The style focuses on patterns that obscure technical meaning and have a clear,
actionable rewrite:

- rhetorical framing that delays a fact or behavior;
- explanatory phrases that restate a point;
- contrastive framing such as "not just X, but Y";
- hollow participial tails such as ", highlighting...";
- formulaic summary beats;
- throat-clearing introductions; and
- claims attributed to unnamed sources.

General documentation requirements remain in the RedHat style. AILanguage
does not check punctuation, emoji, heading capitalization, sentence length,
typography, generic vocabulary, ordinary lists, or paragraph length. Those
signals are either already covered by RedHat or are too broad to be useful
for technical documentation.

## Rule acceptance criteria

A rule belongs in this style only when it:

1. identifies a documented linguistic or structural pattern;
2. reports a specific writing problem and an actionable revision;
3. has an invalid fixture at each expected alert location;
4. has valid Red Hat technical examples that remain clean;
5. does not duplicate an existing RedHat rule; and
6. does not routinely overlap another AILanguage rule.

The corpus in .vale/fixtures/AILanguage/corpus/ represents ordinary concept,
procedure, reference, and general technical prose. The complete style must
produce no alerts for that corpus.

## Sources

The rules draw on the following catalogues of AI-assisted writing patterns:

- *Signs of AI writing*, WikiProject AI Cleanup, Wikipedia.
  https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
- Christian Miles, *Signs of AI writing: a Vale ruleset*, ammil industries.
  https://ammil.industries/signs-of-ai-writing-a-vale-ruleset/
  and the accompanying style at
  https://github.com/ammil-industries/vale-signs-of-ai-writing

Each rule links to the source that documents its pattern.

## Attribution and license

The ammil industries ruleset is released under
[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).
Adapted rules carry an attribution comment.
