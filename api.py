import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import sqlite3

load_dotenv()
DB_NAME = os.getenv("DB_NAME")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class EmployeeSchema(BaseModel):
    name: str
    role: str
    salary: float

@app.post("/employees/")
def create_employee(employee: EmployeeSchema):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO employees (name, role, salary) VALUES (?, ?, ?)",
            (employee.name, employee.role, employee.salary)
        )
        conn.commit()
        conn.close()
        logger.info(f"Accepted POST request for Employee: {employee.name}")
        return {"message": "Employee created successfully"}
    except Exception as e:
        logger.error(f"Error creating employee: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/employees/{emp_id}")
def get_employee(emp_id: int):
    logger.info(f"Accepted GET request for Employee ID {emp_id}")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "role": row[2], "salary": row[3]}
    raise HTTPException(status_code=404, detail="Employee not found")
