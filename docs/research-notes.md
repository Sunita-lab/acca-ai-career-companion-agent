# Research Notes

Project: AI Career Companion Agent for Internship Matching and Interview Preparation (ACCA)
Milestone 1, task M1.1

This document summarises the research behind ACCA's design: how students find internships today, why ACCA uses Retrieval-Augmented Generation (RAG), and why it is built as a set of specialised agents.

---

## 1. Internship Workflow

### How a student finds an internship today

1. The student searches platforms such as Internshala, LinkedIn and Naukri.
2. On each platform they go through a long onboarding: upload a resume, create an account, build a profile and set role preferences.
3. The platform's algorithm then shows a feed based on those preferences, or the student searches and applies to roles manually.
4. Applications lead to shortlisting, a test or interview, and finally an offer (or a rejection).

### Main problems

1. **Fragmented platforms.** Listings are spread across many sites, and the student repeats the same onboarding on each one.
2. **Unclear role fit.** Students often do not know which roles match their resume and skills. Preference filters also assume the student already knows which roles to pick.
3. **Weak preparation.** Students get little help with interview and test preparation, resume quality or cover letters.

### How ACCA addresses these

| Problem | ACCA component |
|---|---|
| Many platforms, repeated search | One job-posting knowledge base and the **Job-Resume Matching Agent**, which ranks internships for a profile |
| Unsure which roles fit | Resume parsing into a structured profile, plus the **Matching Agent** |
| Missing skills for a target role | **Skill Gap Agent** (missing skills with learning suggestions) |
| No interview or test practice | **Interview Agent** (mock interviews, follow-up questions, scoring) |
| Weak resume or cover letter | **Resume Agent** and **Cover Letter Agent** |

In short: the student no longer has to hop between sites. ACCA reads the resume, finds suitable roles, shows the skill gaps and helps with interview preparation.

---

## 2. RAG (Retrieval-Augmented Generation)

### What it is

RAG combines **retrieval** (find the relevant information), **augmentation** (add it to the prompt) and **generation** (the LLM writes the answer). It works like an open-book exam: instead of expecting the model to remember everything, we hand it the right pages at question time.

### Why not give all listings directly to the LLM

- **Context limit.** Thousands of listings do not fit in one prompt.
- **Cost and speed.** Sending every listing on every request is slow and expensive, and uses up tokens.
- **Stale knowledge.** An LLM's training data does not include today's listings, so without retrieval it cannot answer from current postings.

### Why embeddings

Keyword search only matches exact words. A resume line such as "built dashboards in Power BI" and a listing that says "visualization and reporting" mean similar things but share no keywords. Embeddings turn text into vectors so that texts with similar meaning sit close together, which lets us shortlist by meaning, quickly, even over a large collection.

### Roles of retrieval and the LLM

| Step | Job |
|---|---|
| Embedding + vector store | Quickly shortlist the top-k relevant listings from a large set (coarse filter) |
| LLM | Read the shortlist, compare it with the profile, rank it and explain the reasons (the actual reasoning) |

### Pipeline in ACCA

**Preparation (once, and whenever listings change):**
Internship listings -> chunk/clean -> create embeddings -> store in vector store (ChromaDB or FAISS).

**At query time:**
Candidate profile -> create embedding -> retrieve top-k similar listings -> pass the profile and listings to the LLM -> ranked list with reasons.

- **Documents:** internship postings (the job knowledge base).
- **Query:** the structured candidate profile (skills, projects, education).
- **Used by:** the Job-Resume Matching Agent, and the Skill Gap Agent to look up requirements of a target role.

The knowledge base must be updated regularly, otherwise RAG would also return outdated listings.

### Why not only web search

Web search is itself a form of RAG, with the whole internet as the knowledge base. ACCA still prefers a curated knowledge base because:

1. **Control over quality.** We want genuine, clean listings, not random blogs or expired posts.
2. **Structured fields.** Each listing has fixed fields (role, skills, duration, stipend, location), which is hard to extract reliably from messy web pages.
3. **Repeatability.** The same profile should give the same results, which is needed to evaluate ranking quality. Web results change between runs.
4. **Cost and latency.** Vector retrieval is faster and cheaper than searching and reading pages for every query.
5. **Private data.** A student's profile and application history live in our own database, not on the web.
6. **Access limits.** Platforms such as LinkedIn and Internshala are often behind logins or block scraping.

Web search can later be added as an extra tool, so an agent can decide whether the knowledge base is enough or a web search is needed.

### Source of listings

Finding listings is itself a hard problem. For the first version, ACCA will use a sample/curated dataset. Scraping or other sources can be evaluated later.

### When RAG is worth it

RAG pays off when the collection is large and keyword matching is not enough. With only a few dozen listings, they could be passed to the LLM directly.

---

## 3. Multi-Agent Patterns

### Why specialised agents instead of one big prompt

- **Modularity.** Each agent has one job, so it is easier to build, test and improve separately.
- **Easier debugging.** When something goes wrong, we can locate which agent or step failed.
- **Different prompts and tools.** The Interview Agent needs question generation and scoring, the Matching Agent needs the vector store, the Cover Letter Agent needs the profile and a selected listing. One large prompt that tries to do everything becomes confusing and error-prone.

### Router (Career Assistant)

The Career Assistant is the single entry point. It does not do the work itself. It decides which specialised agent should handle the request:

1. The student sends a message.
2. The LLM is asked to classify the request into a category (matching, skill gap, resume review, cover letter, interview).
3. The code calls the agent for that category.

| Student message | Routed to |
|---|---|
| "Find internships for me" | Job-Resume Matching Agent |
| "What should I learn for a data analyst role?" | Skill Gap Agent |
| "Write a cover letter for this company" | Cover Letter Agent |
| "Let me practise for an interview" | Interview Agent |

### Agent vs a normal LLM call

- A **normal LLM call** is one question and one answer. Example: `parse_resume`, which sends resume text and gets JSON back. (It has a small validate-and-retry loop, which is the first agentic element in the project.)
- An **agent** runs the LLM in a **loop** and lets it decide what to do next:
  1. **Tool calling:** the LLM asks for a tool (for example, search the vector store). The surrounding code runs the tool and returns the result to the LLM.
  2. **Memory:** the system stores earlier information (profile, past answers) outside the LLM, for example in the database, and feeds it back in.
  3. **Decision loop:** after seeing a result, the LLM decides whether to call another tool or give the final answer.

Note that tool execution and memory are handled by the code around the LLM, not by the LLM alone. The loop is what makes it an agent.

Example, Interview Agent: ask a question -> read the student's answer -> decide whether to ask a follow-up or move to the next topic -> score the answer.

### Overall flow

Student message -> Career Assistant (router) -> specialised agent -> agent uses tools and memory in a loop -> response.

### Implementation plan

Start with a custom tool-calling loop to understand the mechanics, then compare it with LangGraph. The Matching, Skill Gap and Interview agents get the most depth; the others stay lighter.