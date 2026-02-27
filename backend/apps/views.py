from django.shortcuts import render


def teacher_active_jobs(request):
    jobs = [
        {
            "id": 1,
            "title": "Need Female Tutor for Hifz Revision",
            "description": "My 10-year-old son has memorized 2 Juz. We need a strict teacher for daily revision.",
            "budget": "$10 - $15 / hr",
            "total_bids": 130,
            "posted": "2 Hours Ago",
        },
        {
            "id": 2,
            "title": "Need Online Nazra Teacher",
            "description": "Looking for a patient Quran teacher for beginner-level Nazra classes in the evening.",
            "budget": "$8 - $12 / hr",
            "total_bids": 92,
            "posted": "5 Hours Ago",
        },
        {
            "id": 3,
            "title": "Tajweed Improvement for Teen Student",
            "description": "Need a qualified tutor to improve Tajweed and makharij for a 14-year-old student.",
            "budget": "$12 - $18 / hr",
            "total_bids": 74,
            "posted": "1 Day Ago",
        },
        {
            "id": 4,
            "title": "Weekend Tafsir Classes Needed",
            "description": "Seeking a scholar for weekend Tafsir sessions for a small family group.",
            "budget": "$15 - $20 / hr",
            "total_bids": 41,
            "posted": "3 Hours Ago",
        },
        {
            "id": 5,
            "title": "Female Tutor for Kids Quran Reading",
            "description": "Need a gentle and experienced female tutor for two young children learning Quran reading.",
            "budget": "$9 - $13 / hr",
            "total_bids": 58,
            "posted": "7 Hours Ago",
        },
    ]

    context = {
        "jobs": jobs,
        "total_results": len(jobs),
    }
    return render(request, "bookings/teacher_active_jobs.html", context)

def job_detail(request, job_id):
    jobs = {
        1: {
            "id": 1,
            "title": "Need FemaleHife Tutor for Hifz Revision",
            "description": "I am looking for a qualified Hafiz to teach my 10-year-old son. He has already memorized 2 Juz and needs a strict teacher for daily revision and new lessons. We prefer a teacher who can speak fluent Urdu and English.",
            "budget": "$10 - $15/hr",
            "total_bids": 5,
            "course": "Hifz (Memorization)",
            "schedule": "Mon-Fri, 5:00 PM - 6:00 PM (PKT)",
            "duration": "Long-term",
            "preferred_gender": "Male Tutor",
        },
        2: {
            "id": 2,
            "title": "Need Online Nazra Teacher",
            "description": "Looking for a patient Quran teacher for beginner-level Nazra classes in the evening.",
            "budget": "$8 - $12/hr",
            "total_bids": 3,
            "course": "Nazra",
            "schedule": "Mon-Thu, 7:00 PM - 8:00 PM (PKT)",
            "duration": "3 Months",
            "preferred_gender": "Any",
        },
        3: {
            "id": 3,
            "title": "Tajweed Improvement for Teen Student",
            "description": "Need a qualified tutor to improve Tajweed and makharij for a 14-year-old student.",
            "budget": "$12 - $18/hr",
            "total_bids": 4,
            "course": "Tajweed",
            "schedule": "Sat-Sun, 4:00 PM - 5:00 PM (PKT)",
            "duration": "6 Months",
            "preferred_gender": "Any",
        },
    }

    job = jobs.get(job_id, jobs[1])

    proposals = [
        {
            "name": "Hafiz Abdullah",
            "rating": "4.9",
            "reviews": 23,
            "rate": "$12.00 / hr",
            "availability": "Available Immediately",
            "submitted": "Submitted 1 Hour Ago",
            "image": "",
        },
        {
            "name": "Usman Ghani",
            "rating": "4.9",
            "reviews": 23,
            "rate": "$12.00 / hr",
            "availability": "Available Immediately",
            "submitted": "Submitted 1 Hour Ago",
            "image": "",
        },
        {
            "name": "Zainab Bibi",
            "rating": "4.9",
            "reviews": 23,
            "rate": "$12.00 / hr",
            "availability": "Available Immediately",
            "submitted": "Submitted 1 Hour Ago",
            "image": "",
        },
        {
            "name": "Ahmed Ali",
            "rating": "4.9",
            "reviews": 23,
            "rate": "$12.00 / hr",
            "availability": "Available Immediately",
            "submitted": "Submitted 1 Hour Ago",
            "image": "",
        },
        {
            "name": "Umer Abdullah",
            "rating": "4.9",
            "reviews": 23,
            "rate": "$12.00 / hr",
            "availability": "Available Immediately",
            "submitted": "Submitted 1 Hour Ago",
            "image": "",
        },
    ]
    context = {
        "job": job,
        "proposals": proposals,
    }
    return render(request, "bookings/job_detail.html", context)