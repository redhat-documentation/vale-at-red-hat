# AILanguage

A Vale style that flags the linguistic and structural tells of LLM-generated
prose: filler vocabulary, promotional register, hedged attribution, formulaic
section furniture, and rhythm that comes out too even.

These rules are detection signals for human review. They are not a style guide.
Ordinary human writing trips them, and removing a flagged pattern does not by
itself make a sentence worth reading. Most rules ship at `suggestion` or
`warning` for that reason.

## Sources

The rules draw on three catalogues of AI-writing patterns:

- *Signs of AI writing*, WikiProject AI Cleanup, Wikipedia.
  https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
- Bradley Emi, *Comprehensive Guide to Spotting AI Writing Patterns*, Pangram.
  https://www.pangram.com/blog/comprehensive-guide-to-spotting-ai-writing-patterns
- Christian Miles, *Signs of AI writing: a Vale ruleset*, ammil industries.
  https://ammil.industries/signs-of-ai-writing-a-vale-ruleset/
  and the accompanying style at
  https://github.com/ammil-industries/vale-signs-of-ai-writing

Each rule carries a `link:` to whichever source documents the pattern it catches.

## Attribution and licence

The ammil industries ruleset is released under
[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).
Several rules here are adaptations of rules in that repository.

Adapted rules carries an attribution comment at the top of its file.
