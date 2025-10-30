```markdown
# Company Overview  
**Name:** Aperus  
**Industry:** Software Development / Custom Web & Mobile Solutions  
**Size:** ~50–200 employees (fully remote, cross-timezone teams)  
**Headquarters:** Remote-first (distributed), legally incorporated in the U.S.  

Aperus builds large-scale, high-performance web and mobile applications for clients in fintech, health-tech, e-commerce, and enterprise SaaS. Since its founding in 2018, the company has remained fully asynchronous, leveraging modern cloud and DevOps practices to deliver 24×7 development coverage.  

# Mission and Values  
**Mission:** Empower product teams worldwide through best-in-class asynchronous collaboration and cutting-edge software engineering.  
**Core Values:**  
- *Async First:* Trust in written documentation, async video updates, and clear handoffs over meetings.  
- *Ownership & Autonomy:* Every engineer leads their work; results matter more than presenteeism.  
- *Continuous Improvement:* Invest in tooling, process refinements, code quality, and professional growth.  
- *Diversity & Inclusion:* Hire across geographies, champion diverse perspectives, and foster psychological safety.  

# Recent News or Changes  
- **March 2024:** Aperus announced a $10 M Series A funding round led by CloudVentures to expand its async tooling and hire 40 new engineers.  
- **February 2024:** Launched **Aperus Sync**, an in-house open-source library for building resilient async pipelines on AWS Lambda.  
- **Q1 2024:** Published a blog series on “Scaling FastAPI for Millions of Users” and open-sourced several internal best-practice repos (e.g., async-pruner, ci-watcher).  
- **Late 2023:** Expanded into health-tech vertical; signed two new clients requiring HIPAA-compliant backend architectures.  

# Role Context and Product Involvement  
**Team Structure:**  
- **IC2-level Senior Engineer** reporting to the Engineering Manager of the Backend Guild.  
- Works alongside 3–5 other backend engineers, 2 frontend specialists, and a product manager.  
- Partners with DevOps, Security, and QA on an *asynchronous sprint cadence* (no stand-ups; all planning via written Zaps / tickets).  

**Stack & Responsibilities:**  
- Build and maintain Python-based microservices on FastAPI (and occasionally Django/Flask).  
- Integrate with React/React Native front ends for client-facing dashboards and mobile apps.  
- Own AWS infrastructure components (Lambda, ECS Fargate, RDS, S3), containerized via Docker.  
- Establish and enforce testing (pytest, tox), linting, and CI/CD pipelines in GitHub Actions.  
- Contribute to open-source tooling: async workflows, custom CLI scripts, shared libraries.  

# Likely Interview Topics  
1. **Python & Web Frameworks**  
   - Designing RESTful and GraphQL APIs with FastAPI.  
   - Middleware, dependency injection, performance tuning in Python.  
2. **Asynchronous Patterns**  
   - `async`/`await`, event loops, concurrency vs. parallelism.  
   - Designing retry/backoff strategies for distributed systems.  
3. **Distributed Systems & Microservices**  
   - Service discovery, circuit breakers, idempotency, and transaction management.  
   - Observability: logging, tracing (e.g., OpenTelemetry).  
4. **DevOps & Cloud Infrastructure**  
   - Dockerization best practices; container orchestration (AWS ECS/Fargate).  
   - IaC (Terraform/CloudFormation), CI/CD pipelines, blue/green or canary deployments.  
5. **Collaboration in an Async Culture**  
   - Structuring clear PRs, design docs, and async status updates.  
   - Tools & workflows (GitHub Projects, Linear, Slack, Notion, Loom).  
6. **Full-Stack Integration**  
   - Integrating Python backends with React/React Native front ends.  
   - Managing CORS, authentication (OAuth2, JWT), and real-time updates (WebSockets/Push).  

# Suggested Questions to Ask  
- **Team & Culture**  
  - “How does the async-first approach affect team onboarding and ramp-up?”  
  - “Can you share an example of a cross-functional async workflow that worked particularly well?”  
- **Tech & Architecture**  
  - “What drove the decision to build your own async tooling (Aperus Sync) versus adopting an existing solution?”  
  - “How do you manage schema migrations and versioning across Python microservices?”  
- **Delivery & Quality**  
  - “What is the process for code reviews and how do you measure code quality over time?”  
  - “How are production incidents handled in an async setting—what’s the on-call model?”  
- **Career Growth**  
  - “What does the IC career ladder look like beyond IC2—what skills and responsibilities define the next level?”  
  - “How does Aperus support continuous learning and professional development for remote engineers?”  
- **Future Roadmap**  
  - “Which new verticals or product features is Aperus targeting in the next 6–12 months?”  
  - “How does the team balance client-driven work versus investing in open-source or internal tooling?”  
```