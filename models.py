import sqlite3

class Employee:
    def __init__(self, name, employee_id, salary):
        self.name = name
        self.employee_id = employee_id
        self.salary = salary

    def display_info(self):
        return f"ID: {self.employee_id}, Name: {self.name}, Salary: {self.salary}"

    def save_to_db(self):
        conn = sqlite3.connect('company.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT,
                role TEXT,
                salary REAL
            )
        ''')
        
        cursor.execute("INSERT INTO employees (id, name, role, salary) VALUES (?, ?, ?, ?)", 
                       (self.employee_id, self.name, "Employee", self.salary))
        
        conn.commit()
        conn.close()
        print(f"Employee {self.name} saved to database successfully!")

class Manager(Employee):
    def __init__(self, name, employee_id, salary, department):
        super().__init__(name, employee_id, salary)
        self.department = department

    def display_info(self):
        base_info = super().display_info()
        return f"{base_info}, Department: {self.department}"
