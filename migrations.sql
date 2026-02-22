-- create master user table; plaintext password
create table if not exists users(
	id UUID primary key default gen_random_uuid(),
	email varchar not null,
	password varchar not null
 );

-- create profiles-updated table
create table if not exists profiles(
	id UUID primary key default gen_random_uuid(),
	user_email varchar not null,
	person_name varchar not null,
	person_age int4 not null,
	person_email varchar not null,
	form_path varchar,
	bank_stmt_path varchar,
	id_card_path varchar,
	credit_stmt_path varchar,
	resume_path varchar,
	processing_status varchar default 'in-process'
);
alter table if exists profiles
add column if not exists decision varchar default null
;
alter table if exists profiles
add column if not exists reason varchar default null
;

--drop table if exists profile_extractions

create table if not exists profile_extractions(
	id uuid primary key default gen_random_uuid(),
	profile_id uuid not null,
	extracted_data varchar default null,
	doc_type varchar not null ,
	constraint unique_extraction unique (profile_id, doc_type)
)
;
