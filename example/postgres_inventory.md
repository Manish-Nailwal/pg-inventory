## localhost:5432 · company_db · public.employees

- PostgreSQL Version: PostgreSQL 17.6 on x86_64-windows, compiled by msvc-19.44.35213, 64-bit
- Extensions: plpgsql
- Rowcount: -1
- Primary Key: employee_id

### Columns

| Name | Type | Nullable | Default |
|------|------|----------|---------|
| employee_id | integer | NO | nextval('employees_employee_id_seq'::regclass) |
| first_name | character varying | NO |  |
| last_name | character varying | NO |  |
| email | character varying | NO |  |
| phone_number | character varying | YES |  |
| hire_date | date | NO |  |
| job_title | character varying | YES |  |
| salary | numeric | YES |  |
| department_id | integer | YES |  |

### Indexes
- CREATE UNIQUE INDEX employees_pkey ON public.employees USING btree (employee_id)
- CREATE UNIQUE INDEX employees_email_key ON public.employees USING btree (email)

### Foreign Keys
- fk_department: FOREIGN KEY (department_id) REFERENCES departments(department_id)

---

## localhost:5432 · company_db · public.leave_applications

- PostgreSQL Version: PostgreSQL 17.6 on x86_64-windows, compiled by msvc-19.44.35213, 64-bit
- Extensions: plpgsql
- Rowcount: -1
- Primary Key: leave_id

### Columns

| Name | Type | Nullable | Default |
|------|------|----------|---------|
| leave_id | integer | NO | nextval('leave_applications_leave_id_seq'::regclass) |
| employee_id | integer | NO |  |
| leave_type | character varying | NO |  |
| start_date | date | NO |  |
| end_date | date | NO |  |
| status | character varying | NO |  |
| reason | text | YES |  |

### Indexes
- CREATE UNIQUE INDEX leave_applications_pkey ON public.leave_applications USING btree (leave_id)

### Foreign Keys
- fk_employee: FOREIGN KEY (employee_id) REFERENCES employees(employee_id)

---

## localhost:5432 · company_db · public.departments

- PostgreSQL Version: PostgreSQL 17.6 on x86_64-windows, compiled by msvc-19.44.35213, 64-bit
- Extensions: plpgsql
- Rowcount: -1
- Primary Key: department_id

### Columns

| Name | Type | Nullable | Default |
|------|------|----------|---------|
| department_id | integer | NO | nextval('departments_department_id_seq'::regclass) |
| department_name | character varying | NO |  |
| location | character varying | YES |  |

### Indexes
- CREATE UNIQUE INDEX departments_pkey ON public.departments USING btree (department_id)

---

