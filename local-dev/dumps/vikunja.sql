--
-- PostgreSQL database dump
--

\restrict crwahJ1FxR6BxpRTIXLPAVmvP3UQo7jW6J7mnGyItf9SYZS6gIQFJ1zACY4s1SG

-- Dumped from database version 16.13
-- Dumped by pg_dump version 16.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: api_tokens; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.api_tokens (
    id bigint NOT NULL,
    title character varying(255) NOT NULL,
    token_salt character varying(255) NOT NULL,
    token_hash character varying(255) NOT NULL,
    token_last_eight character varying(8) NOT NULL,
    permissions json NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    created timestamp without time zone NOT NULL,
    owner_id bigint NOT NULL
);


ALTER TABLE public.api_tokens OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: api_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.api_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.api_tokens_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: api_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.api_tokens_id_seq OWNED BY public.api_tokens.id;


--
-- Name: buckets; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.buckets (
    id bigint NOT NULL,
    title text NOT NULL,
    project_view_id bigint NOT NULL,
    "limit" bigint DEFAULT 0,
    "position" double precision,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    created_by_id bigint NOT NULL
);


ALTER TABLE public.buckets OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: buckets_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.buckets_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.buckets_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: buckets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.buckets_id_seq OWNED BY public.buckets.id;


--
-- Name: favorites; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.favorites (
    entity_id bigint NOT NULL,
    user_id bigint NOT NULL,
    kind integer NOT NULL
);


ALTER TABLE public.favorites OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: files; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.files (
    id bigint NOT NULL,
    name text NOT NULL,
    mime text,
    size bigint NOT NULL,
    created timestamp without time zone,
    created_by_id bigint NOT NULL
);


ALTER TABLE public.files OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: files_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.files_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.files_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: files_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.files_id_seq OWNED BY public.files.id;


--
-- Name: label_tasks; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.label_tasks (
    id bigint NOT NULL,
    task_id bigint NOT NULL,
    label_id bigint NOT NULL,
    created timestamp without time zone NOT NULL
);


ALTER TABLE public.label_tasks OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: label_tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.label_tasks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.label_tasks_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: label_tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.label_tasks_id_seq OWNED BY public.label_tasks.id;


--
-- Name: labels; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.labels (
    id bigint NOT NULL,
    title character varying(250) NOT NULL,
    description text,
    hex_color character varying(6),
    created_by_id bigint NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL
);


ALTER TABLE public.labels OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: labels_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.labels_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.labels_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: labels_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.labels_id_seq OWNED BY public.labels.id;


--
-- Name: link_shares; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.link_shares (
    id bigint NOT NULL,
    hash character varying(40) NOT NULL,
    name text,
    project_id bigint NOT NULL,
    permission bigint DEFAULT 0 NOT NULL,
    sharing_type bigint DEFAULT 0 NOT NULL,
    password text,
    shared_by_id bigint NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL
);


ALTER TABLE public.link_shares OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: link_shares_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.link_shares_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.link_shares_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: link_shares_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.link_shares_id_seq OWNED BY public.link_shares.id;


--
-- Name: migration; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.migration (
    id character varying(255),
    description character varying(255)
);


ALTER TABLE public.migration OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: migration_status; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.migration_status (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    migrator_name character varying(255),
    started_at timestamp without time zone NOT NULL,
    finished_at timestamp without time zone
);


ALTER TABLE public.migration_status OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: migration_status_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.migration_status_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.migration_status_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: migration_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.migration_status_id_seq OWNED BY public.migration_status.id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.notifications (
    id bigint NOT NULL,
    notifiable_id bigint NOT NULL,
    notification json NOT NULL,
    name character varying(250) NOT NULL,
    subject_id bigint,
    read_at timestamp without time zone,
    created timestamp without time zone NOT NULL
);


ALTER TABLE public.notifications OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.notifications_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notifications_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: project_views; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.project_views (
    id bigint NOT NULL,
    title character varying(255) NOT NULL,
    project_id bigint NOT NULL,
    view_kind integer NOT NULL,
    filter json,
    "position" double precision,
    bucket_configuration_mode integer DEFAULT 0,
    bucket_configuration json,
    default_bucket_id bigint,
    done_bucket_id bigint,
    updated timestamp without time zone NOT NULL,
    created timestamp without time zone NOT NULL
);


ALTER TABLE public.project_views OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: project_views_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.project_views_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.project_views_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: project_views_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.project_views_id_seq OWNED BY public.project_views.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.projects (
    id bigint NOT NULL,
    title character varying(250) NOT NULL,
    description text,
    identifier character varying(10),
    hex_color character varying(6),
    owner_id bigint NOT NULL,
    parent_project_id bigint,
    is_archived boolean DEFAULT false NOT NULL,
    background_file_id bigint,
    background_blur_hash character varying(50),
    "position" double precision,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL
);


ALTER TABLE public.projects OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.projects_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.projects_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: reactions; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.reactions (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    entity_id bigint NOT NULL,
    entity_kind bigint NOT NULL,
    value character varying(20) NOT NULL,
    created timestamp without time zone NOT NULL
);


ALTER TABLE public.reactions OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: reactions_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.reactions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reactions_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: reactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.reactions_id_seq OWNED BY public.reactions.id;


--
-- Name: saved_filters; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.saved_filters (
    id bigint NOT NULL,
    filters json NOT NULL,
    title character varying(250) NOT NULL,
    description text,
    owner_id bigint NOT NULL,
    is_favorite boolean DEFAULT false,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL
);


ALTER TABLE public.saved_filters OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: saved_filters_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.saved_filters_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.saved_filters_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: saved_filters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.saved_filters_id_seq OWNED BY public.saved_filters.id;


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.sessions (
    id character varying(36) NOT NULL,
    user_id bigint NOT NULL,
    token_hash character varying(64) NOT NULL,
    device_info text,
    ip_address character varying(100),
    is_long_session boolean DEFAULT false NOT NULL,
    last_active timestamp without time zone NOT NULL,
    created timestamp without time zone NOT NULL
);


ALTER TABLE public.sessions OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.subscriptions (
    id bigint NOT NULL,
    entity_type integer NOT NULL,
    entity_id bigint NOT NULL,
    user_id bigint NOT NULL,
    created timestamp without time zone NOT NULL
);


ALTER TABLE public.subscriptions OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: subscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.subscriptions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.subscriptions_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.subscriptions_id_seq OWNED BY public.subscriptions.id;


--
-- Name: task_assignees; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.task_assignees (
    id bigint NOT NULL,
    task_id bigint NOT NULL,
    user_id bigint NOT NULL,
    created timestamp without time zone NOT NULL
);


ALTER TABLE public.task_assignees OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: task_assignees_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.task_assignees_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.task_assignees_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: task_assignees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.task_assignees_id_seq OWNED BY public.task_assignees.id;


--
-- Name: task_attachments; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.task_attachments (
    id bigint NOT NULL,
    task_id bigint NOT NULL,
    file_id bigint NOT NULL,
    created_by_id bigint NOT NULL,
    created timestamp without time zone
);


ALTER TABLE public.task_attachments OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: task_attachments_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.task_attachments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.task_attachments_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: task_attachments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.task_attachments_id_seq OWNED BY public.task_attachments.id;


--
-- Name: task_buckets; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.task_buckets (
    bucket_id bigint NOT NULL,
    task_id bigint NOT NULL,
    project_view_id bigint NOT NULL
);


ALTER TABLE public.task_buckets OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: task_comments; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.task_comments (
    id bigint NOT NULL,
    comment text NOT NULL,
    author_id bigint NOT NULL,
    task_id bigint NOT NULL,
    created timestamp without time zone,
    updated timestamp without time zone
);


ALTER TABLE public.task_comments OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: task_comments_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.task_comments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.task_comments_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: task_comments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.task_comments_id_seq OWNED BY public.task_comments.id;


--
-- Name: task_positions; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.task_positions (
    task_id bigint NOT NULL,
    project_view_id bigint NOT NULL,
    "position" double precision NOT NULL
);


ALTER TABLE public.task_positions OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: task_relations; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.task_relations (
    id bigint NOT NULL,
    task_id bigint NOT NULL,
    other_task_id bigint NOT NULL,
    relation_kind character varying(50) NOT NULL,
    created_by_id bigint NOT NULL,
    created timestamp without time zone NOT NULL
);


ALTER TABLE public.task_relations OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: task_relations_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.task_relations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.task_relations_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: task_relations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.task_relations_id_seq OWNED BY public.task_relations.id;


--
-- Name: task_reminders; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.task_reminders (
    id bigint NOT NULL,
    task_id bigint NOT NULL,
    reminder timestamp without time zone NOT NULL,
    created timestamp without time zone NOT NULL,
    relative_period bigint,
    relative_to character varying(50)
);


ALTER TABLE public.task_reminders OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: task_reminders_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.task_reminders_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.task_reminders_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: task_reminders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.task_reminders_id_seq OWNED BY public.task_reminders.id;


--
-- Name: task_unread_statuses; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.task_unread_statuses (
    task_id bigint NOT NULL,
    user_id bigint NOT NULL
);


ALTER TABLE public.task_unread_statuses OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: tasks; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.tasks (
    id bigint NOT NULL,
    title text NOT NULL,
    description text,
    done boolean,
    done_at timestamp without time zone,
    due_date timestamp without time zone,
    project_id bigint NOT NULL,
    repeat_after bigint,
    repeat_mode integer DEFAULT 0 NOT NULL,
    priority bigint,
    start_date timestamp without time zone,
    end_date timestamp without time zone,
    hex_color character varying(6),
    percent_done double precision,
    index bigint DEFAULT 0 NOT NULL,
    uid character varying(250),
    cover_image_attachment_id bigint DEFAULT 0,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    created_by_id bigint NOT NULL
);


ALTER TABLE public.tasks OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.tasks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tasks_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.tasks_id_seq OWNED BY public.tasks.id;


--
-- Name: team_members; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.team_members (
    id bigint NOT NULL,
    team_id bigint NOT NULL,
    user_id bigint NOT NULL,
    admin boolean,
    created timestamp without time zone NOT NULL
);


ALTER TABLE public.team_members OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: team_members_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.team_members_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.team_members_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: team_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.team_members_id_seq OWNED BY public.team_members.id;


--
-- Name: team_projects; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.team_projects (
    id bigint NOT NULL,
    team_id bigint NOT NULL,
    project_id bigint NOT NULL,
    permission bigint DEFAULT 0 NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL
);


ALTER TABLE public.team_projects OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: team_projects_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.team_projects_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.team_projects_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: team_projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.team_projects_id_seq OWNED BY public.team_projects.id;


--
-- Name: teams; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.teams (
    id bigint NOT NULL,
    name character varying(250) NOT NULL,
    description text,
    created_by_id bigint NOT NULL,
    external_id character varying(250),
    issuer text,
    created timestamp without time zone,
    updated timestamp without time zone,
    is_public boolean DEFAULT false NOT NULL
);


ALTER TABLE public.teams OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: teams_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.teams_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.teams_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: teams_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.teams_id_seq OWNED BY public.teams.id;


--
-- Name: totp; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.totp (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    secret text NOT NULL,
    enabled boolean,
    url text
);


ALTER TABLE public.totp OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: totp_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.totp_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.totp_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: totp_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.totp_id_seq OWNED BY public.totp.id;


--
-- Name: unsplash_photos; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.unsplash_photos (
    id bigint NOT NULL,
    file_id bigint NOT NULL,
    unsplash_id character varying(50),
    author text,
    author_name text
);


ALTER TABLE public.unsplash_photos OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: unsplash_photos_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.unsplash_photos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.unsplash_photos_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: unsplash_photos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.unsplash_photos_id_seq OWNED BY public.unsplash_photos.id;


--
-- Name: user_tokens; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.user_tokens (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    token character varying(450) NOT NULL,
    kind integer NOT NULL,
    created timestamp without time zone NOT NULL
);


ALTER TABLE public.user_tokens OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: user_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.user_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_tokens_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: user_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.user_tokens_id_seq OWNED BY public.user_tokens.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.users (
    id bigint NOT NULL,
    name text,
    username character varying(250) NOT NULL,
    password character varying(250),
    email character varying(250),
    status integer DEFAULT 0,
    avatar_provider character varying(255),
    avatar_file_id bigint,
    issuer text,
    subject text,
    email_reminders_enabled boolean DEFAULT true,
    discoverable_by_name boolean DEFAULT false,
    discoverable_by_email boolean DEFAULT false,
    overdue_tasks_reminders_enabled boolean DEFAULT true,
    overdue_tasks_reminders_time character varying(5) DEFAULT '09:00'::character varying NOT NULL,
    default_project_id bigint,
    week_start integer,
    language character varying(50),
    timezone character varying(255),
    deletion_scheduled_at timestamp without time zone,
    deletion_last_reminder_sent timestamp without time zone,
    frontend_settings json,
    extra_settings_links json,
    export_file_id bigint,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL
);


ALTER TABLE public.users OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: users_projects; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.users_projects (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    project_id bigint NOT NULL,
    permission bigint DEFAULT 0 NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL
);


ALTER TABLE public.users_projects OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: users_projects_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.users_projects_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_projects_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: users_projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.users_projects_id_seq OWNED BY public.users_projects.id;


--
-- Name: webhooks; Type: TABLE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE TABLE public.webhooks (
    id bigint NOT NULL,
    target_url character varying(255) NOT NULL,
    events json NOT NULL,
    project_id bigint NOT NULL,
    secret character varying(255),
    basic_auth_user character varying(255),
    basic_auth_password character varying(255),
    created_by_id bigint NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL
);


ALTER TABLE public.webhooks OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: webhooks_id_seq; Type: SEQUENCE; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE SEQUENCE public.webhooks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webhooks_id_seq OWNER TO "5Dxd6byzJJTdaaHY";

--
-- Name: webhooks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER SEQUENCE public.webhooks_id_seq OWNED BY public.webhooks.id;


--
-- Name: api_tokens id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.api_tokens ALTER COLUMN id SET DEFAULT nextval('public.api_tokens_id_seq'::regclass);


--
-- Name: buckets id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.buckets ALTER COLUMN id SET DEFAULT nextval('public.buckets_id_seq'::regclass);


--
-- Name: files id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.files ALTER COLUMN id SET DEFAULT nextval('public.files_id_seq'::regclass);


--
-- Name: label_tasks id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.label_tasks ALTER COLUMN id SET DEFAULT nextval('public.label_tasks_id_seq'::regclass);


--
-- Name: labels id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.labels ALTER COLUMN id SET DEFAULT nextval('public.labels_id_seq'::regclass);


--
-- Name: link_shares id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.link_shares ALTER COLUMN id SET DEFAULT nextval('public.link_shares_id_seq'::regclass);


--
-- Name: migration_status id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.migration_status ALTER COLUMN id SET DEFAULT nextval('public.migration_status_id_seq'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: project_views id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.project_views ALTER COLUMN id SET DEFAULT nextval('public.project_views_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: reactions id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.reactions ALTER COLUMN id SET DEFAULT nextval('public.reactions_id_seq'::regclass);


--
-- Name: saved_filters id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.saved_filters ALTER COLUMN id SET DEFAULT nextval('public.saved_filters_id_seq'::regclass);


--
-- Name: subscriptions id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.subscriptions ALTER COLUMN id SET DEFAULT nextval('public.subscriptions_id_seq'::regclass);


--
-- Name: task_assignees id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.task_assignees ALTER COLUMN id SET DEFAULT nextval('public.task_assignees_id_seq'::regclass);


--
-- Name: task_attachments id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.task_attachments ALTER COLUMN id SET DEFAULT nextval('public.task_attachments_id_seq'::regclass);


--
-- Name: task_comments id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.task_comments ALTER COLUMN id SET DEFAULT nextval('public.task_comments_id_seq'::regclass);


--
-- Name: task_relations id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.task_relations ALTER COLUMN id SET DEFAULT nextval('public.task_relations_id_seq'::regclass);


--
-- Name: task_reminders id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.task_reminders ALTER COLUMN id SET DEFAULT nextval('public.task_reminders_id_seq'::regclass);


--
-- Name: tasks id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.tasks ALTER COLUMN id SET DEFAULT nextval('public.tasks_id_seq'::regclass);


--
-- Name: team_members id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.team_members ALTER COLUMN id SET DEFAULT nextval('public.team_members_id_seq'::regclass);


--
-- Name: team_projects id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.team_projects ALTER COLUMN id SET DEFAULT nextval('public.team_projects_id_seq'::regclass);


--
-- Name: teams id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.teams ALTER COLUMN id SET DEFAULT nextval('public.teams_id_seq'::regclass);


--
-- Name: totp id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.totp ALTER COLUMN id SET DEFAULT nextval('public.totp_id_seq'::regclass);


--
-- Name: unsplash_photos id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.unsplash_photos ALTER COLUMN id SET DEFAULT nextval('public.unsplash_photos_id_seq'::regclass);


--
-- Name: user_tokens id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.user_tokens ALTER COLUMN id SET DEFAULT nextval('public.user_tokens_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: users_projects id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.users_projects ALTER COLUMN id SET DEFAULT nextval('public.users_projects_id_seq'::regclass);


--
-- Name: webhooks id; Type: DEFAULT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.webhooks ALTER COLUMN id SET DEFAULT nextval('public.webhooks_id_seq'::regclass);


--
-- Data for Name: api_tokens; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.api_tokens (id, title, token_salt, token_hash, token_last_eight, permissions, expires_at, created, owner_id) FROM stdin;
\.


--
-- Data for Name: buckets; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.buckets (id, title, project_view_id, "limit", "position", created, updated, created_by_id) FROM stdin;
1	To-Do	4	0	100	2026-03-07 17:00:55	2026-03-07 17:00:55	1
2	Doing	4	0	200	2026-03-07 17:00:55	2026-03-07 17:00:55	1
3	Done	4	0	300	2026-03-07 17:00:55	2026-03-07 17:00:55	1
4	To-Do	8	0	100	2026-03-07 17:04:37	2026-03-07 17:04:37	1
5	Doing	8	0	200	2026-03-07 17:04:37	2026-03-07 17:04:37	1
6	Done	8	0	300	2026-03-07 17:04:37	2026-03-07 17:04:37	1
\.


--
-- Data for Name: favorites; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.favorites (entity_id, user_id, kind) FROM stdin;
\.


--
-- Data for Name: files; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.files (id, name, mime, size, created, created_by_id) FROM stdin;
\.


--
-- Data for Name: label_tasks; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.label_tasks (id, task_id, label_id, created) FROM stdin;
\.


--
-- Data for Name: labels; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.labels (id, title, description, hex_color, created_by_id, created, updated) FROM stdin;
\.


--
-- Data for Name: link_shares; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.link_shares (id, hash, name, project_id, permission, sharing_type, password, shared_by_id, created, updated) FROM stdin;
\.


--
-- Data for Name: migration; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.migration (id, description) FROM stdin;
SCHEMA_INIT	
20190324205606	
20190328074430	
20190430111111	
20190511202210	
20190514192749	
20190524205441	
20190718200716	
20190818210133	
20190920185205	
20190922205826	
20191008194238	
20191010131430	
20191207204427	
20191207220736	
20200120201756	
20200219183248	
20200308205855	
20200308210130	
20200322214440	
20200322214624	
20200417175201	
20200418230432	
20200418230605	
20200420215928	
20200425182634	
20200509103709	
20200515172220	
20200515195546	
20200516123847	
20200524221534	
20200524224611	
20200614113230	
20200621214452	
20200801183357	
20200904101559	
20200905151040	
20200905232458	
20200906184746	
20201025195822	
20201121181647	
20201218152741	
20201218220204	
20201219145028	
20210207192805	
20210209204715	
20210220222121	
20210221111953	
20210321185225	
20210328191017	
20210403145503	
20210403220653	
20210407170753	
20210411113105	
20210411161337	
20210413131057	
20210527105701	
20210603174608	
20210709191101	
20210709211508	
20210711173657	
20210713213622	
20210725153703	
20210727204942	
20210727211037	
20210729142940	
20210802081716	
20210829194722	
20211212151642	
20211212210054	
20220112211537	
20220616145228	
20220815200851	
20221002120521	
20221113170740	
20221228112131	
20230104152903	
20230307171848	
20230611170341	
20230824132533	
20230828125443	
20230831155832	
20230903143017	
20230913202615	
20231022144641	
20231108231513	
20231121191822	
20240114224713	
20240304153738	
20240309111148	
20240311173251	
20240313230538	
20240314214802	
20240315093418	
20240315104205	
20240315110428	
20240329170952	
20240406125227	
20240603172746	
20240919130957	
20241028131622	
20241118123644	
20241119115012	
20250317174522	
20250323212553	
20250402173109	
20250624092830	
20250813093602	
20251001113831	
20251108154913	
20251118125156	
20260123000717	
20260224113347	
20260224122023	
20260225114726	
\.


--
-- Data for Name: migration_status; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.migration_status (id, user_id, migrator_name, started_at, finished_at) FROM stdin;
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.notifications (id, notifiable_id, notification, name, subject_id, read_at, created) FROM stdin;
\.


--
-- Data for Name: project_views; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.project_views (id, title, project_id, view_kind, filter, "position", bucket_configuration_mode, bucket_configuration, default_bucket_id, done_bucket_id, updated, created) FROM stdin;
1	List	1	0	{"s":"","sort_by":null,"order_by":null,"filter":"done = false","filter_include_nulls":false}	100	0	null	0	0	2026-03-07 17:00:55	2026-03-07 17:00:55
2	Gantt	1	1	\N	200	0	null	0	0	2026-03-07 17:00:55	2026-03-07 17:00:55
3	Table	1	2	\N	300	0	null	0	0	2026-03-07 17:00:55	2026-03-07 17:00:55
4	Kanban	1	3	\N	400	1	null	1	3	2026-03-07 17:00:55	2026-03-07 17:00:55
5	List	2	0	{"s":"","sort_by":null,"order_by":null,"filter":"done = false","filter_include_nulls":false}	100	0	null	0	0	2026-03-07 17:04:37	2026-03-07 17:04:37
6	Gantt	2	1	\N	200	0	null	0	0	2026-03-07 17:04:37	2026-03-07 17:04:37
7	Table	2	2	\N	300	0	null	0	0	2026-03-07 17:04:37	2026-03-07 17:04:37
8	Kanban	2	3	\N	400	1	null	4	6	2026-03-07 17:04:37	2026-03-07 17:04:37
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.projects (id, title, description, identifier, hex_color, owner_id, parent_project_id, is_archived, background_file_id, background_blur_hash, "position", created, updated) FROM stdin;
1	Inbox				1	0	f	0		65536	2026-03-07 17:00:55	2026-03-07 17:00:55
2	Server setup				1	0	f	0		131072	2026-03-07 17:04:37	2026-03-09 08:13:09
\.


--
-- Data for Name: reactions; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.reactions (id, user_id, entity_id, entity_kind, value, created) FROM stdin;
\.


--
-- Data for Name: saved_filters; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.saved_filters (id, filters, title, description, owner_id, is_favorite, created, updated) FROM stdin;
\.


--
-- Data for Name: sessions; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.sessions (id, user_id, token_hash, device_info, ip_address, is_long_session, last_active, created) FROM stdin;
cfaff64a-0a1a-47a5-a3f4-11b28db6cc89	1	996d7bc61fb325bb3dadf436388a35e65df0fd15f1808de2d35e0b30476491f8	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.3.1 Safari/605.1.15	46.59.70.243	f	2026-03-07 17:00:56	2026-03-07 17:00:56
1bfb92d3-6d77-41f1-a8bd-69cd38e085fc	1	0e18a9ccc97e0c38bc268770f4cbd69393782ccf0f71571edd3866a2d2c6646e	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	46.59.70.243	f	2026-03-07 17:08:06	2026-03-07 17:08:06
c6baff85-11d1-43db-9144-473ddd22dabe	1	609f54d7bd8d17be01deb5987d730bfa886494f00264d87322091a955f5d41ae	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	46.59.70.243	t	2026-03-07 17:12:23	2026-03-07 17:12:23
b809a18e-a0b3-499d-9b39-0ee5434f87b1	1	27b95335f271a542e124631468b7a093f4d3d3086798c47fd499e504c5e2c453	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	46.59.70.243	t	2026-03-09 08:13:06	2026-03-07 17:12:37
23050e37-4ac6-425d-af33-46c02dc00378	1	4b6fcbd314ab6bfe8275563a502840da32e9c7fb4fa62c4fc26dd26608b5597e	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.3.1 Safari/605.1.15	46.59.70.243	t	2026-03-08 09:25:35	2026-03-07 17:08:57
\.


--
-- Data for Name: subscriptions; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.subscriptions (id, entity_type, entity_id, user_id, created) FROM stdin;
\.


--
-- Data for Name: task_assignees; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.task_assignees (id, task_id, user_id, created) FROM stdin;
\.


--
-- Data for Name: task_attachments; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.task_attachments (id, task_id, file_id, created_by_id, created) FROM stdin;
\.


--
-- Data for Name: task_buckets; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.task_buckets (bucket_id, task_id, project_view_id) FROM stdin;
4	3	8
6	2	8
6	1	8
6	4	8
\.


--
-- Data for Name: task_comments; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.task_comments (id, comment, author_id, task_id, created, updated) FROM stdin;
\.


--
-- Data for Name: task_positions; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.task_positions (task_id, project_view_id, "position") FROM stdin;
1	5	65536
1	6	65536
1	7	65536
2	5	32768
2	6	32768
2	7	32768
3	5	16384
3	6	16384
3	7	16384
3	8	16384
4	5	8192
4	6	8192
4	7	8192
2	8	131072
1	8	65536
4	8	262144
\.


--
-- Data for Name: task_relations; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.task_relations (id, task_id, other_task_id, relation_kind, created_by_id, created) FROM stdin;
\.


--
-- Data for Name: task_reminders; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.task_reminders (id, task_id, reminder, created, relative_period, relative_to) FROM stdin;
\.


--
-- Data for Name: task_unread_statuses; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.task_unread_statuses (task_id, user_id) FROM stdin;
\.


--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.tasks (id, title, description, done, done_at, due_date, project_id, repeat_after, repeat_mode, priority, start_date, end_date, hex_color, percent_done, index, uid, cover_image_attachment_id, created, updated, created_by_id) FROM stdin;
3	Test Vikunja		f	\N	\N	2	0	0	0	\N	\N		0	3	300392ee-5b22-4f84-a5e2-6b8b045ddf20	0	2026-03-07 17:05:25	2026-03-07 17:05:25	1
2	Test OpenProject		t	2026-03-09 08:12:53	\N	2	0	0	0	\N	\N		0	2	dc60acbd-729f-446b-ab09-40b48b9495ec	0	2026-03-07 17:05:12	2026-03-09 08:12:53	1
1	Deploy Nextcloud		t	2026-03-09 08:12:58	\N	2	0	0	0	2026-03-06 11:00:00	\N		0.5	1	7f9840a2-5f35-4d2b-b7a4-68706b855e0f	0	2026-03-07 17:04:58	2026-03-09 08:12:58	1
4	Deploy Kimai		t	2026-03-09 08:13:09	\N	2	0	0	0	\N	\N		0	4	2dfcb8da-14a7-4230-82df-5a5c1adca105	0	2026-03-07 17:05:45	2026-03-09 08:13:09	1
\.


--
-- Data for Name: team_members; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.team_members (id, team_id, user_id, admin, created) FROM stdin;
\.


--
-- Data for Name: team_projects; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.team_projects (id, team_id, project_id, permission, created, updated) FROM stdin;
\.


--
-- Data for Name: teams; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.teams (id, name, description, created_by_id, external_id, issuer, created, updated, is_public) FROM stdin;
\.


--
-- Data for Name: totp; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.totp (id, user_id, secret, enabled, url) FROM stdin;
\.


--
-- Data for Name: unsplash_photos; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.unsplash_photos (id, file_id, unsplash_id, author, author_name) FROM stdin;
\.


--
-- Data for Name: user_tokens; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.user_tokens (id, user_id, token, kind, created) FROM stdin;
1	1	MC4pgX2DNlLjmOABqpTxM2o3Wx6MfLND0LzIZzFok1HK30Uai50ZgIpYwKGxIRAU	2	2026-03-07 17:00:55
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.users (id, name, username, password, email, status, avatar_provider, avatar_file_id, issuer, subject, email_reminders_enabled, discoverable_by_name, discoverable_by_email, overdue_tasks_reminders_enabled, overdue_tasks_reminders_time, default_project_id, week_start, language, timezone, deletion_scheduled_at, deletion_last_reminder_sent, frontend_settings, extra_settings_links, export_file_id, created, updated) FROM stdin;
1		stephan	$2a$11$fqIDUBSpYOK6zz1nk54cPeXgH/xXyi.muwTv40JHaPCKI3rLVfaMG	stephan@edumusik.com	0	initials	0	local		f	f	f	t	9:00	1	0	en	GMT	\N	\N	null	null	0	2026-03-07 17:00:55	2026-03-07 17:00:55
\.


--
-- Data for Name: users_projects; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.users_projects (id, user_id, project_id, permission, created, updated) FROM stdin;
\.


--
-- Data for Name: webhooks; Type: TABLE DATA; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

COPY public.webhooks (id, target_url, events, project_id, secret, basic_auth_user, basic_auth_password, created_by_id, created, updated) FROM stdin;
\.


--
-- Name: api_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.api_tokens_id_seq', 1, false);


--
-- Name: buckets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.buckets_id_seq', 6, true);


--
-- Name: files_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.files_id_seq', 1, false);


--
-- Name: label_tasks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.label_tasks_id_seq', 1, false);


--
-- Name: labels_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.labels_id_seq', 1, false);


--
-- Name: link_shares_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.link_shares_id_seq', 1, false);


--
-- Name: migration_status_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.migration_status_id_seq', 1, false);


--
-- Name: notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.notifications_id_seq', 1, false);


--
-- Name: project_views_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.project_views_id_seq', 8, true);


--
-- Name: projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.projects_id_seq', 2, true);


--
-- Name: reactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.reactions_id_seq', 1, false);


--
-- Name: saved_filters_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.saved_filters_id_seq', 1, false);


--
-- Name: subscriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.subscriptions_id_seq', 1, false);


--
-- Name: task_assignees_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.task_assignees_id_seq', 1, false);


--
-- Name: task_attachments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.task_attachments_id_seq', 1, false);


--
-- Name: task_comments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.task_comments_id_seq', 1, false);


--
-- Name: task_relations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.task_relations_id_seq', 1, false);


--
-- Name: task_reminders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.task_reminders_id_seq', 1, false);


--
-- Name: tasks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.tasks_id_seq', 4, true);


--
-- Name: team_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.team_members_id_seq', 1, false);


--
-- Name: team_projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.team_projects_id_seq', 1, false);


--
-- Name: teams_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.teams_id_seq', 1, false);


--
-- Name: totp_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.totp_id_seq', 1, false);


--
-- Name: unsplash_photos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.unsplash_photos_id_seq', 1, false);


--
-- Name: user_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.user_tokens_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: users_projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.users_projects_id_seq', 1, false);


--
-- Name: webhooks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

SELECT pg_catalog.setval('public.webhooks_id_seq', 1, false);


--
-- Name: api_tokens api_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.api_tokens
    ADD CONSTRAINT api_tokens_pkey PRIMARY KEY (id);


--
-- Name: buckets buckets_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.buckets
    ADD CONSTRAINT buckets_pkey PRIMARY KEY (id);


--
-- Name: favorites favorites_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT favorites_pkey PRIMARY KEY (entity_id, user_id, kind);


--
-- Name: files files_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_pkey PRIMARY KEY (id);


--
-- Name: label_tasks label_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.label_tasks
    ADD CONSTRAINT label_tasks_pkey PRIMARY KEY (id);


--
-- Name: labels labels_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.labels
    ADD CONSTRAINT labels_pkey PRIMARY KEY (id);


--
-- Name: link_shares link_shares_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.link_shares
    ADD CONSTRAINT link_shares_pkey PRIMARY KEY (id);


--
-- Name: migration_status migration_status_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.migration_status
    ADD CONSTRAINT migration_status_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: project_views project_views_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.project_views
    ADD CONSTRAINT project_views_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: reactions reactions_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.reactions
    ADD CONSTRAINT reactions_pkey PRIMARY KEY (id);


--
-- Name: saved_filters saved_filters_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.saved_filters
    ADD CONSTRAINT saved_filters_pkey PRIMARY KEY (id);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (id);


--
-- Name: task_assignees task_assignees_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.task_assignees
    ADD CONSTRAINT task_assignees_pkey PRIMARY KEY (id);


--
-- Name: task_attachments task_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.task_attachments
    ADD CONSTRAINT task_attachments_pkey PRIMARY KEY (id);


--
-- Name: task_comments task_comments_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.task_comments
    ADD CONSTRAINT task_comments_pkey PRIMARY KEY (id);


--
-- Name: task_relations task_relations_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.task_relations
    ADD CONSTRAINT task_relations_pkey PRIMARY KEY (id);


--
-- Name: task_reminders task_reminders_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.task_reminders
    ADD CONSTRAINT task_reminders_pkey PRIMARY KEY (id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: team_members team_members_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_pkey PRIMARY KEY (id);


--
-- Name: team_projects team_projects_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.team_projects
    ADD CONSTRAINT team_projects_pkey PRIMARY KEY (id);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (id);


--
-- Name: totp totp_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.totp
    ADD CONSTRAINT totp_pkey PRIMARY KEY (id);


--
-- Name: unsplash_photos unsplash_photos_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.unsplash_photos
    ADD CONSTRAINT unsplash_photos_pkey PRIMARY KEY (id);


--
-- Name: user_tokens user_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.user_tokens
    ADD CONSTRAINT user_tokens_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users_projects users_projects_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.users_projects
    ADD CONSTRAINT users_projects_pkey PRIMARY KEY (id);


--
-- Name: webhooks webhooks_pkey; Type: CONSTRAINT; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

ALTER TABLE ONLY public.webhooks
    ADD CONSTRAINT webhooks_pkey PRIMARY KEY (id);


--
-- Name: IDX_api_tokens_token_last_eight; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_api_tokens_token_last_eight" ON public.api_tokens USING btree (token_last_eight);


--
-- Name: IDX_label_tasks_label_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_label_tasks_label_id" ON public.label_tasks USING btree (label_id);


--
-- Name: IDX_label_tasks_task_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_label_tasks_task_id" ON public.label_tasks USING btree (task_id);


--
-- Name: IDX_link_shares_permission; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_link_shares_permission" ON public.link_shares USING btree (permission);


--
-- Name: IDX_link_shares_shared_by_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_link_shares_shared_by_id" ON public.link_shares USING btree (shared_by_id);


--
-- Name: IDX_link_shares_sharing_type; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_link_shares_sharing_type" ON public.link_shares USING btree (sharing_type);


--
-- Name: IDX_notifications_name; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_notifications_name" ON public.notifications USING btree (name);


--
-- Name: IDX_project_views_default_bucket_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_project_views_default_bucket_id" ON public.project_views USING btree (default_bucket_id);


--
-- Name: IDX_project_views_done_bucket_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_project_views_done_bucket_id" ON public.project_views USING btree (done_bucket_id);


--
-- Name: IDX_project_views_project_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_project_views_project_id" ON public.project_views USING btree (project_id);


--
-- Name: IDX_projects_owner_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_projects_owner_id" ON public.projects USING btree (owner_id);


--
-- Name: IDX_projects_parent_project_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_projects_parent_project_id" ON public.projects USING btree (parent_project_id);


--
-- Name: IDX_reactions_entity_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_reactions_entity_id" ON public.reactions USING btree (entity_id);


--
-- Name: IDX_reactions_entity_kind; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_reactions_entity_kind" ON public.reactions USING btree (entity_kind);


--
-- Name: IDX_reactions_user_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_reactions_user_id" ON public.reactions USING btree (user_id);


--
-- Name: IDX_reactions_value; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_reactions_value" ON public.reactions USING btree (value);


--
-- Name: IDX_saved_filters_owner_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_saved_filters_owner_id" ON public.saved_filters USING btree (owner_id);


--
-- Name: IDX_sessions_user_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_sessions_user_id" ON public.sessions USING btree (user_id);


--
-- Name: IDX_subscriptions_entity_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_subscriptions_entity_id" ON public.subscriptions USING btree (entity_id);


--
-- Name: IDX_subscriptions_entity_type; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_subscriptions_entity_type" ON public.subscriptions USING btree (entity_type);


--
-- Name: IDX_subscriptions_user_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_subscriptions_user_id" ON public.subscriptions USING btree (user_id);


--
-- Name: IDX_task_assignees_task_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_task_assignees_task_id" ON public.task_assignees USING btree (task_id);


--
-- Name: IDX_task_assignees_user_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_task_assignees_user_id" ON public.task_assignees USING btree (user_id);


--
-- Name: IDX_task_buckets_bucket_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_task_buckets_bucket_id" ON public.task_buckets USING btree (bucket_id);


--
-- Name: IDX_task_buckets_project_view_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_task_buckets_project_view_id" ON public.task_buckets USING btree (project_view_id);


--
-- Name: IDX_task_buckets_task_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_task_buckets_task_id" ON public.task_buckets USING btree (task_id);


--
-- Name: IDX_task_comments_task_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_task_comments_task_id" ON public.task_comments USING btree (task_id);


--
-- Name: IDX_task_positions_project_view_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_task_positions_project_view_id" ON public.task_positions USING btree (project_view_id);


--
-- Name: IDX_task_positions_task_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_task_positions_task_id" ON public.task_positions USING btree (task_id);


--
-- Name: IDX_task_reminders_reminder; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_task_reminders_reminder" ON public.task_reminders USING btree (reminder);


--
-- Name: IDX_task_reminders_task_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_task_reminders_task_id" ON public.task_reminders USING btree (task_id);


--
-- Name: IDX_tasks_done; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_tasks_done" ON public.tasks USING btree (done);


--
-- Name: IDX_tasks_done_at; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_tasks_done_at" ON public.tasks USING btree (done_at);


--
-- Name: IDX_tasks_due_date; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_tasks_due_date" ON public.tasks USING btree (due_date);


--
-- Name: IDX_tasks_end_date; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_tasks_end_date" ON public.tasks USING btree (end_date);


--
-- Name: IDX_tasks_project_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_tasks_project_id" ON public.tasks USING btree (project_id);


--
-- Name: IDX_tasks_repeat_after; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_tasks_repeat_after" ON public.tasks USING btree (repeat_after);


--
-- Name: IDX_tasks_start_date; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_tasks_start_date" ON public.tasks USING btree (start_date);


--
-- Name: IDX_team_members_team_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_team_members_team_id" ON public.team_members USING btree (team_id);


--
-- Name: IDX_team_members_user_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_team_members_user_id" ON public.team_members USING btree (user_id);


--
-- Name: IDX_team_projects_permission; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_team_projects_permission" ON public.team_projects USING btree (permission);


--
-- Name: IDX_team_projects_project_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_team_projects_project_id" ON public.team_projects USING btree (project_id);


--
-- Name: IDX_team_projects_team_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_team_projects_team_id" ON public.team_projects USING btree (team_id);


--
-- Name: IDX_teams_created_by_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_teams_created_by_id" ON public.teams USING btree (created_by_id);


--
-- Name: IDX_user_tokens_token; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_user_tokens_token" ON public.user_tokens USING btree (token);


--
-- Name: IDX_users_default_project_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_users_default_project_id" ON public.users USING btree (default_project_id);


--
-- Name: IDX_users_discoverable_by_email; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_users_discoverable_by_email" ON public.users USING btree (discoverable_by_email);


--
-- Name: IDX_users_discoverable_by_name; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_users_discoverable_by_name" ON public.users USING btree (discoverable_by_name);


--
-- Name: IDX_users_overdue_tasks_reminders_enabled; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_users_overdue_tasks_reminders_enabled" ON public.users USING btree (overdue_tasks_reminders_enabled);


--
-- Name: IDX_users_projects_permission; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_users_projects_permission" ON public.users_projects USING btree (permission);


--
-- Name: IDX_users_projects_project_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_users_projects_project_id" ON public.users_projects USING btree (project_id);


--
-- Name: IDX_users_projects_user_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_users_projects_user_id" ON public.users_projects USING btree (user_id);


--
-- Name: IDX_webhooks_project_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE INDEX "IDX_webhooks_project_id" ON public.webhooks USING btree (project_id);


--
-- Name: UQE_api_tokens_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_api_tokens_id" ON public.api_tokens USING btree (id);


--
-- Name: UQE_api_tokens_token_hash; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_api_tokens_token_hash" ON public.api_tokens USING btree (token_hash);


--
-- Name: UQE_buckets_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_buckets_id" ON public.buckets USING btree (id);


--
-- Name: UQE_files_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_files_id" ON public.files USING btree (id);


--
-- Name: UQE_label_tasks_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_label_tasks_id" ON public.label_tasks USING btree (id);


--
-- Name: UQE_labels_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_labels_id" ON public.labels USING btree (id);


--
-- Name: UQE_link_shares_hash; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_link_shares_hash" ON public.link_shares USING btree (hash);


--
-- Name: UQE_link_shares_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_link_shares_id" ON public.link_shares USING btree (id);


--
-- Name: UQE_migration_status_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_migration_status_id" ON public.migration_status USING btree (id);


--
-- Name: UQE_notifications_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_notifications_id" ON public.notifications USING btree (id);


--
-- Name: UQE_project_views_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_project_views_id" ON public.project_views USING btree (id);


--
-- Name: UQE_projects_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_projects_id" ON public.projects USING btree (id);


--
-- Name: UQE_reactions_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_reactions_id" ON public.reactions USING btree (id);


--
-- Name: UQE_saved_filters_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_saved_filters_id" ON public.saved_filters USING btree (id);


--
-- Name: UQE_sessions_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_sessions_id" ON public.sessions USING btree (id);


--
-- Name: UQE_sessions_token_hash; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_sessions_token_hash" ON public.sessions USING btree (token_hash);


--
-- Name: UQE_subscriptions_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_subscriptions_id" ON public.subscriptions USING btree (id);


--
-- Name: UQE_task_assignees_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_task_assignees_id" ON public.task_assignees USING btree (id);


--
-- Name: UQE_task_attachments_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_task_attachments_id" ON public.task_attachments USING btree (id);


--
-- Name: UQE_task_buckets_task_view; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_task_buckets_task_view" ON public.task_buckets USING btree (task_id, project_view_id);


--
-- Name: UQE_task_comments_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_task_comments_id" ON public.task_comments USING btree (id);


--
-- Name: UQE_task_relations_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_task_relations_id" ON public.task_relations USING btree (id);


--
-- Name: UQE_task_reminders_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_task_reminders_id" ON public.task_reminders USING btree (id);


--
-- Name: UQE_task_unread_statuses_task_user; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_task_unread_statuses_task_user" ON public.task_unread_statuses USING btree (task_id, user_id);


--
-- Name: UQE_tasks_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_tasks_id" ON public.tasks USING btree (id);


--
-- Name: UQE_team_members_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_team_members_id" ON public.team_members USING btree (id);


--
-- Name: UQE_team_projects_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_team_projects_id" ON public.team_projects USING btree (id);


--
-- Name: UQE_teams_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_teams_id" ON public.teams USING btree (id);


--
-- Name: UQE_totp_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_totp_id" ON public.totp USING btree (id);


--
-- Name: UQE_unsplash_photos_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_unsplash_photos_id" ON public.unsplash_photos USING btree (id);


--
-- Name: UQE_user_tokens_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_user_tokens_id" ON public.user_tokens USING btree (id);


--
-- Name: UQE_users_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_users_id" ON public.users USING btree (id);


--
-- Name: UQE_users_projects_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_users_projects_id" ON public.users_projects USING btree (id);


--
-- Name: UQE_users_username; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_users_username" ON public.users USING btree (username);


--
-- Name: UQE_webhooks_id; Type: INDEX; Schema: public; Owner: 5Dxd6byzJJTdaaHY
--

CREATE UNIQUE INDEX "UQE_webhooks_id" ON public.webhooks USING btree (id);


--
-- PostgreSQL database dump complete
--

\unrestrict crwahJ1FxR6BxpRTIXLPAVmvP3UQo7jW6J7mnGyItf9SYZS6gIQFJ1zACY4s1SG

