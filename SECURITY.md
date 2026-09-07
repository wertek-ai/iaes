# Security

IAES is a specification. Most of what looks like a security question here is
either a defect in a document, which belongs in the open, or a defect in
somebody's software, which does not.

## Which of the two you have

**A defect in an implementation** — an SDK that mishandles input, a parser that
can be made to crash, a node that leaks a credential it was given. That is
software, and it goes to **engineering@wertek.ai** rather than into an issue.

Include the package and version, what you sent, and what happened. There is no
bounty. You will get an answer.

**A defect in the standard** — a constraint that says one thing and enforces
another, an enumeration that cannot express what it claims to, a field whose
absence means something it should not, a `format` that describes rather than
asserts. **These belong in the open**, as an issue or an RFC.

They are not vulnerabilities and treating them as secrets makes the standard
worse: everybody implementing IAES has the same defect, and the only fix is one
everybody can read. Several such defects are recorded in this repository's own
RFCs with the measurement that found them.

## What IAES does not define, and therefore cannot get wrong

**Transport security.** IAES defines no transport, no endpoint contract and no
delivery negotiation. There is no TLS story here because there is no wire here
— an IAES event is a shape, and how it travels belongs to whatever carries it.

An implementation that publishes events in the clear is not violating this
standard. It may well be a bad idea, and its own documentation should say so;
that is between it and its users.

**Authentication and authorization.** IAES carries no identity, no credential
and no permission model. `source` names a producer for the reader's benefit; it
authenticates nothing and MUST NOT be treated as though it did.

## What must never go in an issue

**No credentials.** No API keys, tokens, passwords or connection strings, even
expired ones, even in a stack trace.

**No data from a real installation.** Not a plant name, not a site, not an
asset identifier, not a customer's. Use `acme.*`, `Planta Norte`, `VFD-001` —
the examples in this repository are written that way on purpose.

This is not a formality. A public repository keeps what it is given: rewriting
a branch does not remove it, and a pull request reference outlives a forced
push. Getting a plant name back out of a public repository means creating a new
one, and even then the old objects were served to anyone who asked while they
were there.

If something like that has already been posted, mail **engineering@wertek.ai**
rather than deleting the comment. Deleting it does not remove it, and knowing
what to clean up is worth more than a tidy thread.

## Scope

This repository: the specification, its schemas, and the SDKs published from
it. Reference implementations live in their own repositories and carry their
own `SECURITY.md`; a defect in one of those belongs there.
