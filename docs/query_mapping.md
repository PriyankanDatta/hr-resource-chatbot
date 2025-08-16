# Query → Structured Mapping (v1)

**Extraction targets (v1)**
- skills: [string]
- min_experience_years: int (default: 0)
- domains: [string]
- availability: one of {"available","soon","unavailable"} (default: any)

**Examples**
1. "React Native project, need someone 3+ years"  
   -> skills: ["react native"], min_experience_years: 3, domains: [], availability: any

2. "Python dev with AWS for ecommerce"  
   -> skills: ["python","aws"], domains: ["ecommerce"], min_experience_years: 0, availability: any

3. "Who is available with healthcare background?"  
   -> availability: "available", domains: ["healthcare"]

4. "Suggest people for a backend service on Docker and Postgres"  
   -> skills: ["docker","postgres"], domains: ["backend"], min_experience_years: 0
