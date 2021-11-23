create table users (
  id      serial primary key,
  name    text not null unique,
  token   uuid not null unique default gen_random_uuid(),
  created timestamptz not null default now(),
  profile jsonb not null default '{}'
);

create table tasks (
  id       serial primary key,
  user_id  integer not null references users(id) on delete cascade,
  created  timestamptz not null default now(),
  started  timestamptz,
  finished timestamptz,
  method   text not null,
  url      text not null,
  status   text not null default 'PENDING',
  result   boolean,
  message  text
);

create index on tasks (id, status);
