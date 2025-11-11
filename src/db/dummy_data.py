"""Initialize database with dummy data for testing and demo purposes."""

from datetime import datetime, timedelta
from uuid import uuid4
from . import crud

def init_dummy_data():
    """Populate the in-memory database with sample users, jobs, candidates, and assessments."""
    
    # === 1. CREATE SAMPLE USERS ===
    user1 = crud.create_user({
        "email": "alice@techcorp.com",
        "full_name": "Alice Johnson",
        "password": "password123",
        "org_id": "test-org-1",
        "is_active": True,
    })
    
    user2 = crud.create_user({
        "email": "bob@techcorp.com",
        "full_name": "Bob Smith",
        "password": "password123",
        "org_id": "test-org-1",
        "is_active": True,
    })
    
    # === 2. CREATE SAMPLE JOBS ===
    job1 = crud.create_job_post({
        "title": "Senior Python Developer",
        "location": "San Francisco, CA",
        "description": "We are looking for a Senior Python Developer with 5+ years of experience in building scalable web applications using FastAPI and Django. Strong knowledge of Docker, Kubernetes, and cloud services (AWS, GCP) required. Must have experience with PostgreSQL and Redis.",
        "required_skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Docker", "AWS"],
        "min_experience_years": 5,
        "salary_range_min": 120000,
        "salary_range_max": 180000,
        "status": "ACTIVE",
    }, "test-org-1")
    
    job2 = crud.create_job_post({
        "title": "Frontend Engineer",
        "location": "Remote",
        "description": "Seeking a Frontend Engineer with expertise in React, TypeScript, and modern CSS frameworks. Experience with state management tools (Redux, Zustand) and testing libraries (Jest, React Testing Library) is essential. You should have a passion for creating responsive and accessible user interfaces.",
        "required_skills": ["React", "TypeScript", "JavaScript", "CSS", "Redux", "Jest"],
        "min_experience_years": 3,
        "salary_range_min": 100000,
        "salary_range_max": 150000,
        "status": "ACTIVE",
    }, "test-org-1")
    
    job3 = crud.create_job_post({
        "title": "Data Scientist",
        "location": "New York, NY",
        "description": "Join our data team to build machine learning models and data pipelines. Required: Strong Python skills, experience with pandas, numpy, scikit-learn, and TensorFlow. Knowledge of SQL and big data tools (Spark, Hadoop) is a plus. PhD in Computer Science or related field preferred.",
        "required_skills": ["Python", "Machine Learning", "TensorFlow", "pandas", "SQL", "Spark"],
        "min_experience_years": 4,
        "salary_range_min": 130000,
        "salary_range_max": 190000,
        "status": "ACTIVE",
    }, "test-org-1")
    
    # === 3. CREATE SAMPLE CANDIDATES ===
    # For Senior Python Developer
    candidate1 = crud.create_candidate({
        "full_name": "Sarah Connor",
        "email": "sarah.connor@email.com",
        "cv_text": "Sarah Connor - Senior Software Engineer\n\nExperience:\n- 6 years as Senior Python Developer at TechCorp\n- Built scalable APIs using FastAPI and Django\n- Docker and Kubernetes deployment experience\n- AWS certified solutions architect\n- Led team of 5 developers\n- PostgreSQL and Redis optimization expert\n\nSkills: Python, FastAPI, Django, PostgreSQL, Docker, Kubernetes, AWS, Git\nEducation: BS in Computer Science from MIT",
        "stage": "APPLIED",
        "application_date": datetime.now() - timedelta(days=2),
    }, job1["id"])
    
    candidate2 = crud.create_candidate({
        "full_name": "John Doe",
        "email": "john.doe@email.com",
        "cv_text": "John Doe - Python Developer\n\nExperience:\n- 3 years as Python Developer at StartupXYZ\n- Built REST APIs with Flask\n- Some Docker experience\n- Basic AWS knowledge\n- MongoDB database experience\n\nSkills: Python, Flask, Docker, MongoDB, JavaScript, HTML/CSS\nEducation: BS in Information Technology from State University",
        "stage": "APPLIED",
        "application_date": datetime.now() - timedelta(days=1),
    }, job1["id"])
    
    # For Frontend Engineer
    candidate3 = crud.create_candidate({
        "full_name": "Emma Wilson",
        "email": "emma.wilson@email.com",
        "cv_text": "Emma Wilson - Senior Frontend Engineer\n\nExperience:\n- 5 years as Frontend Engineer at WebCorp\n- Expert in React and TypeScript\n- Built accessible UIs following WCAG standards\n- Redux and Context API proficiency\n- Jest and React Testing Library expert\n- CSS-in-JS and responsive design specialist\n\nSkills: React, TypeScript, JavaScript, CSS3, Redux, Jest, React Testing Library, Webpack\nEducation: BS in Web Development from Design Academy",
        "stage": "APPLIED",
        "application_date": datetime.now() - timedelta(days=3),
    }, job2["id"])
    
    # For Data Scientist
    candidate4 = crud.create_candidate({
        "full_name": "Dr. Michael Chen",
        "email": "michael.chen@email.com",
        "cv_text": "Dr. Michael Chen - Data Scientist\n\nExperience:\n- PhD in Machine Learning from Stanford\n- 7 years in ML/AI research and development\n- Expert in TensorFlow, PyTorch, and scikit-learn\n- Built recommendation systems using deep learning\n- Big data pipeline development with Spark\n- SQL optimization and data warehouse design\n- Published 15+ papers in top ML conferences\n\nSkills: Python, TensorFlow, scikit-learn, pandas, Spark, SQL, Docker, AWS SageMaker\nEducation: PhD in Machine Learning, BS in Mathematics",
        "stage": "APPLIED",
        "application_date": datetime.now() - timedelta(days=5),
    }, job3["id"])
    
    # === 4. CREATE SCREENING RESULTS ===
    for candidate in [candidate1, candidate2, candidate3, candidate4]:
        # Simulate AI screening results
        if candidate["full_name"] == "Sarah Connor":
            result = {
                "candidate_id": candidate["id"],
                "job_id": candidate["job_post_id"],
                "ats_score": 92,
                "feedback": "Excellent match! 6 years of directly relevant Python/FastAPI experience. All required skills present. Strong background with AWS and Docker. Ready for interview.",
                "highlights": ["FastAPI", "Django", "AWS", "Docker", "Kubernetes", "PostgreSQL", "Redis"],
                "strengths": ["Leadership experience", "AWS certified", "Strong technical depth"],
                "gaps": [],
            }
        elif candidate["full_name"] == "John Doe":
            result = {
                "candidate_id": candidate["id"],
                "job_id": candidate["job_post_id"],
                "ats_score": 58,
                "feedback": "Partial match. Has Python experience but lacks FastAPI expertise (Flask background). Limited AWS/Docker experience. May need ramp-up time. Consider for junior/mid-level positions.",
                "highlights": ["Python", "Docker", "MongoDB"],
                "strengths": ["Python fundamentals", "REST API experience"],
                "gaps": ["FastAPI", "Advanced AWS", "Kubernetes", "PostgreSQL"],
            }
        elif candidate["full_name"] == "Emma Wilson":
            result = {
                "candidate_id": candidate["id"],
                "job_id": candidate["job_post_id"],
                "ats_score": 88,
                "feedback": "Strong match! 5 years of React/TypeScript experience. Excellent testing knowledge with Jest and RTL. Accessibility expertise is a bonus. Ready for senior role.",
                "highlights": ["React", "TypeScript", "Jest", "React Testing Library", "CSS3", "Redux"],
                "strengths": ["Accessibility focus", "Testing expertise", "Modern tooling knowledge"],
                "gaps": [],
            }
        else:  # Dr. Michael Chen
            result = {
                "candidate_id": candidate["id"],
                "job_id": candidate["job_post_id"],
                "ats_score": 95,
                "feedback": "Exceptional match! PhD in Machine Learning with 7+ years experience. Expert in all required tools. Published researcher. Significantly overqualified but perfect fit.",
                "highlights": ["TensorFlow", "scikit-learn", "Spark", "SQL", "Python", "AWS SageMaker"],
                "strengths": ["PhD background", "Research publications", "Deep learning expertise", "Big data experience"],
                "gaps": [],
            }
        
        crud.create_screening_result(result)
    
    # === 5. CREATE SAMPLE ASSESSMENTS ===
    assessment1 = crud.create_assessment({
        "candidate_id": candidate1["id"],
        "job_id": job1["id"],
        "generated_questions": [
            {"question": "Explain the difference between sync and async in Python. How would you implement async/await in a FastAPI endpoint?", "type": "open-ended"},
            {"question": "Design a scalable database schema for a multi-tenant SaaS application. What indexing strategies would you use?", "type": "open-ended"},
            {"question": "How would you optimize a slow PostgreSQL query that joins 5 tables?", "type": "technical"},
            {"question": "Describe your experience with Docker and Kubernetes in production environments.", "type": "experience"},
        ],
        "status": "SENT",
        "created_at": datetime.now() - timedelta(hours=2),
    })
    
    assessment2 = crud.create_assessment({
        "candidate_id": candidate3["id"],
        "job_id": job2["id"],
        "generated_questions": [
            {"question": "Build a React component that fetches user data from an API and displays it in a table with sorting and filtering.", "type": "coding"},
            {"question": "Explain your approach to state management. When would you use Redux vs Context API?", "type": "technical"},
            {"question": "How do you ensure your React components are accessible? What tools and practices do you use?", "type": "technical"},
            {"question": "Write unit tests for a custom React hook.", "type": "coding"},
        ],
        "status": "SENT",
        "created_at": datetime.now() - timedelta(hours=1),
    })
    
    # === 6. CREATE SAMPLE INTERVIEWS ===
    interview1 = crud.create_interview({
        "candidate_id": candidate1["id"],
        "job_id": job1["id"],
        "scheduled_time": datetime.now() + timedelta(days=3, hours=10),
        "interviewer_name": "Tech Lead - Robert Johnson",
        "interview_format": "Technical + Behavioral",
        "duration_minutes": 60,
        "status": "SCHEDULED",
        "meeting_link": "https://meet.google.com/abc-defg-hij",
    })
    
    interview2 = crud.create_interview({
        "candidate_id": candidate3["id"],
        "job_id": job2["id"],
        "scheduled_time": datetime.now() + timedelta(days=2, hours=14),
        "interviewer_name": "Engineering Manager - Lisa Wong",
        "interview_format": "Technical + System Design",
        "duration_minutes": 90,
        "status": "SCHEDULED",
        "meeting_link": "https://meet.google.com/xyz-uvwx-stu",
    })
    
    print("✅ Dummy data initialized successfully!")
    print(f"  - Created {len(crud.DATABASE['users'])} users")
    print(f"  - Created {len(crud.DATABASE['jobs'])} jobs")
    print(f"  - Created {len(crud.DATABASE['candidates'])} candidates")
    print(f"  - Created {len(crud.DATABASE['screening_results'])} screening results")
    print(f"  - Created {len(crud.DATABASE['assessments'])} assessments")
    print(f"  - Created {len(crud.DATABASE['interviews'])} interviews")
