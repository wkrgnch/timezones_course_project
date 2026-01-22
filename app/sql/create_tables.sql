CREATE TABLE IF NOT EXISTS timezones (
    fias_code text PRIMARY KEY,
    region text NOT NULL,
    region_norm text NOT NULL,
    msk_offset_hours int NOT NULL DEFAULT 0,
    utc_offset_hours int NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS users (
    id bigserial PRIMARY KEY,
    full_name text NOT NULL,
    email text NOT NULL UNIQUE,
    role text NOT NULL CHECK (role in ('student','teacher')),
    password_hash text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS groups (
    id bigserial PRIMARY KEY,
    teacher_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_number text NOT NULL,
    join_code text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS participants (
    id bigserial PRIMARY KEY,
    group_id bigint NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id bigint REFERENCES users(id) ON DELETE SET NULL,
    display_name text NOT NULL,
    region text NULL,
    msk_offset_hours int NULL,
    joined_at timestamptz NOT NULL DEFAULT now(),
    position int NOT NULL DEFAULT 0
);