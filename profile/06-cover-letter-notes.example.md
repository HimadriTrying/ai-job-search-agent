# Cover Letter Notes

Copy this to `profile/06-cover-letter-notes.md` (gitignored) and fill in the sections marked
**YOURS**. Everything above those is the house spec, enforced by
`scripts/check-cover-letter.sh`. Read it before drafting; the checker only catches the
mechanical half.

---

## The shape: one story in four beats, 200 to 280 words

**It is one story, not four paragraphs.** Four self-contained paragraphs read as a list even
when every one of them is true, and a list has no argument in it. A letter works when the
reader can retell it in one sentence to someone else in the room, because that is what
actually happens to the letters that work.

**The spine: something specific you found out about them, which your own experience answers.**
Set it up in beat 1, pay it off in beat 4. That payoff is the callback, and it is the whole
difference between a letter written *for* them and a letter written *at* them.

**Beat 1. The observation.** One or two sentences. Open on the researched point, stated as
something you noticed, not as background. Never "I am writing to apply", never enthusiasm,
never a description of what they do.

**Beat 2. The proof. One flagship, everything else is a clause.** The thing you have done
that answers the observation. Numbers live here and only here. The commonest failure is
listing three achievements at equal weight, which leaves the reader to pick, and they won't.

**Beat 3. The turn.** A different *kind* of proof, not more of the same. If the flagship was
scale, this is zero-to-one, or the regulated craft, or the rebuild nobody wanted. This beat
carries the cost as well as the win; a story with no cost in it reads as a brochure.

**Beat 4. The callback, and what you want next.** Return to the beat 1 observation, now
answered, then say what you want to own. If the closing line would still be true of their
competitor, it is not researched, it is filler.

## The researched point: what qualifies

The hardest thing here to satisfy, and the one carrying the conversion. Four tests, all of
which have to pass.

1. **Only real research would surface it.** Not the homepage, not the About page, not the
   funding round that was in the press. A changelog, a conference talk, a job posting for the
   team next door, a regulatory filing, a founder interview, a product decision only visible
   from actually using the thing. If it took under five minutes to find, they have seen it in
   a hundred other letters.
2. **It relates to the role or the domain.** A charming fact about their office is
   disqualifying. The point has to sit inside the problem space you are applying into,
   otherwise you have done research *at* them rather than *about the job*.
3. **It is married to your experience.** Show the join; do not cite the fact and move on.
   **The test: delete the researched sentence. If the rest of the letter still stands
   unchanged, the research was decoration.**
4. **It does not explain them to themselves.** No "you are building", no company background.
   State it the way a peer would, assuming everything they already know.

**It has to be sourced.** The point must trace to the `company-research` skill's output. The
checker requires that file to exist and requires the letter to share ground with it, because
a "researched closer" rule that nothing verifies is decoration: a letter can otherwise pass
every check on a company nobody ever researched.

## Rules the checker enforces

1. **No dashes as punctuation.** No em dash, no en dash, no spaced hyphen standing in for
   one. Hyphens inside words are fine: product-led, zero-to-one.
2. **200 to 280 words.** Longer is not more convincing, it is less read.
3. **No selling register**, no generic enthusiasm, no self-aware pre-emption ("you might be
   wondering why"). State the reasoning directly.
4. **Don't explain the company to the company.**
5. **The right company name**, checked against every other company you have researched.
6. **Every figure traces to `career_facts.yaml`.** Complementary to `honesty/verify.py`.
7. **No sentence over 35 words.** It is read in a voice.
8. **Beats must not all open with "I."** That is the tell that they are modules, not beats.

Run it:

```bash
bash scripts/check-cover-letter.sh <letter.md> --company <name>
```

**Passing is a floor, not a verdict.** See `docs/FAILURE-MODES.md`.

---

## YOURS: recurring angles that work for me
<!-- e.g. "connect my platform experience to their scaling problem" -->

## YOURS: signature stories (short)
<!-- 2-3 anecdotes you can adapt. Reference STAR stories in 07 by name.
     Mark which is your flagship (beat 2) and which works as a turn (beat 3). -->

## YOURS: hard nos
<!-- Things you refuse to claim or say, even if they'd help. Protects authenticity. -->
