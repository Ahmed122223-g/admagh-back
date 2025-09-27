# app/routers/ai.py - الكود المصحح باستخدام httpx

import os
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import httpx # <--- استخدام مكتبة httpx غير المتزامنة
from dotenv import load_dotenv

# لضمان تحميل مفتاح API
load_dotenv()

# --- تعريف النماذج (Schema) ---

# نموذج البيانات الذي نتوقع أن يرجعه Gemini
class GeminiTaskAnalysis(BaseModel):
    name: str = Field(..., description="عنوان المهمة")
    description: str = Field(..., description="الوصف التفصيلي للمهمة")
    type: str = Field(..., description="نوع المهمة: urgent | important | routine | other") 
    scheduledFor: str = Field(..., description="متى يجب جدولتها: today | tomorrow | week | month")
    classification: str = Field(..., description="تصنيف المهمة (مثل: work, personal, learning)")
    estimatedHours: float = Field(..., description="الوقت المقدر بالساعات (رقم عشري)")

class TaskAnalysisRequest(BaseModel):
    text: str = Field(..., description="النص المدخل من المستخدم لتحليله")

# --- تهيئة الراوتر ---

router = APIRouter(
    prefix="/ai",
    tags=["الذكاء الاصطناعي (Gemini)"],
)

# الحصول على مفتاح API من متغيرات البيئة
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    # يجب أن يكون هذا المفتاح موجوداً في ملف .env
    print("WARNING: GEMINI_API_KEY is not set.")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# --- وظائف تحليل الرد ---

def parse_gemini_response(result: dict) -> List[GeminiTaskAnalysis]:
    """يستخلص JSON من استجابة Gemini ويتحقق من صحته."""
    try:
        # استخراج النص من الاستجابة المتوقعة
        text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        
        # تحميل JSON
        tasks_data = json.loads(text.strip())
        
        # يجب أن نتأكد من أن البيانات هي قائمة (List)
        if not isinstance(tasks_data, list):
            tasks_data = [tasks_data]
            
        # التحقق من صحة البيانات باستخدام Pydantic (تتم تلقائياً في FastAPI)
        # لكن التحويل اليدوي يضمن أننا نتحقق من البيانات قبل إرجاعها
        # يتم التحقق النهائي من Pydantic تلقائيا عند إرجاع الـ response
        
        return tasks_data
        
    except (KeyError, IndexError):
        raise HTTPException(status_code=500, detail="Gemini response structure is invalid.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Gemini did not return valid JSON.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unknown error occurred during parsing: {e}")

# --- المسار الرئيسي ---

@router.post('/gemini/analyze-tasks', response_model=List[GeminiTaskAnalysis])
async def analyze_tasks(req: TaskAnalysisRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Gemini API key is missing from server configuration.")
        
    prompt = (
        "Analyze the following user input and return a JSON array of tasks. "
        "The response must be *only* a JSON array (no markdown, no backticks, no extra text). "
        "Respond in the same language as the user's input. "
        "Each task must strictly adhere to the following JSON keys and types: name(str), description(str), "
        "type(str: urgent|important|routine|other), scheduledFor(str: today|tomorrow|week|month), "
        "classification(str), and estimatedHours(float). "
        f"User input to analyze:\n{req.text}"
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    print("Gemini payload:", payload)
    
    # استخدام httpx غير المتزامن
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            GEMINI_API_URL, 
            json=payload,
            params={"key": GEMINI_API_KEY}
        )
        try:
            response.raise_for_status() # إلقاء خطأ لطلبات HTTP الفاشلة (4xx, 5xx)
        except httpx.HTTPStatusError as e:
            print("Gemini API error response:", response.text)
            raise

    result = response.json()
    return parse_gemini_response(result)
