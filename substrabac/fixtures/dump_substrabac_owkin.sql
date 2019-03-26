--
-- PostgreSQL database dump
--

-- Dumped from database version 10.4 (Ubuntu 10.4-0ubuntu0.18.04)
-- Dumped by pg_dump version 10.4 (Ubuntu 10.4-0ubuntu0.18.04)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner:
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(80) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO substrabac;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: substrabac
--

CREATE SEQUENCE public.auth_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_group_id_seq OWNER TO substrabac;

--
-- Name: auth_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: substrabac
--

ALTER SEQUENCE public.auth_group_id_seq OWNED BY public.auth_group.id;


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.auth_group_permissions (
    id integer NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO substrabac;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: substrabac
--

CREATE SEQUENCE public.auth_group_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_group_permissions_id_seq OWNER TO substrabac;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: substrabac
--

ALTER SEQUENCE public.auth_group_permissions_id_seq OWNED BY public.auth_group_permissions.id;


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO substrabac;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: substrabac
--

CREATE SEQUENCE public.auth_permission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_permission_id_seq OWNER TO substrabac;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: substrabac
--

ALTER SEQUENCE public.auth_permission_id_seq OWNED BY public.auth_permission.id;


--
-- Name: auth_user; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(30) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


ALTER TABLE public.auth_user OWNER TO substrabac;

--
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.auth_user_groups (
    id integer NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.auth_user_groups OWNER TO substrabac;

--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: substrabac
--

CREATE SEQUENCE public.auth_user_groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_user_groups_id_seq OWNER TO substrabac;

--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: substrabac
--

ALTER SEQUENCE public.auth_user_groups_id_seq OWNED BY public.auth_user_groups.id;


--
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: substrabac
--

CREATE SEQUENCE public.auth_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_user_id_seq OWNER TO substrabac;

--
-- Name: auth_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: substrabac
--

ALTER SEQUENCE public.auth_user_id_seq OWNED BY public.auth_user.id;


--
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.auth_user_user_permissions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_user_user_permissions OWNER TO substrabac;

--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: substrabac
--

CREATE SEQUENCE public.auth_user_user_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_user_user_permissions_id_seq OWNER TO substrabac;

--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: substrabac
--

ALTER SEQUENCE public.auth_user_user_permissions_id_seq OWNED BY public.auth_user_user_permissions.id;


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO substrabac;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: substrabac
--

CREATE SEQUENCE public.django_admin_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_admin_log_id_seq OWNER TO substrabac;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: substrabac
--

ALTER SEQUENCE public.django_admin_log_id_seq OWNED BY public.django_admin_log.id;


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO substrabac;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: substrabac
--

CREATE SEQUENCE public.django_content_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_content_type_id_seq OWNER TO substrabac;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: substrabac
--

ALTER SEQUENCE public.django_content_type_id_seq OWNED BY public.django_content_type.id;


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.django_migrations (
    id integer NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO substrabac;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: substrabac
--

CREATE SEQUENCE public.django_migrations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_migrations_id_seq OWNER TO substrabac;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: substrabac
--

ALTER SEQUENCE public.django_migrations_id_seq OWNED BY public.django_migrations.id;


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO substrabac;

--
-- Name: django_site; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.django_site (
    id integer NOT NULL,
    domain character varying(100) NOT NULL,
    name character varying(50) NOT NULL
);


ALTER TABLE public.django_site OWNER TO substrabac;

--
-- Name: django_site_id_seq; Type: SEQUENCE; Schema: public; Owner: substrabac
--

CREATE SEQUENCE public.django_site_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_site_id_seq OWNER TO substrabac;

--
-- Name: django_site_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: substrabac
--

ALTER SEQUENCE public.django_site_id_seq OWNED BY public.django_site.id;


--
-- Name: substrapp_algo; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.substrapp_algo (
    pkhash character varying(64) NOT NULL,
    file character varying(500) NOT NULL,
    description character varying(500) NOT NULL,
    validated boolean NOT NULL
);


ALTER TABLE public.substrapp_algo OWNER TO substrabac;

--
-- Name: substrapp_challenge; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.substrapp_challenge (
    creation_date timestamp with time zone NOT NULL,
    last_modified timestamp with time zone NOT NULL,
    pkhash character varying(64) NOT NULL,
    validated boolean NOT NULL,
    description character varying(500),
    metrics character varying(500)
);


ALTER TABLE public.substrapp_challenge OWNER TO substrabac;

--
-- Name: substrapp_data; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.substrapp_data (
    pkhash character varying(64) NOT NULL,
    validated boolean NOT NULL,
    file character varying(500) NOT NULL
);


ALTER TABLE public.substrapp_data OWNER TO substrabac;

--
-- Name: substrapp_dataset; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.substrapp_dataset (
    pkhash character varying(64) NOT NULL,
    name character varying(24) NOT NULL,
    data_opener character varying(500) NOT NULL,
    description character varying(500) NOT NULL,
    validated boolean NOT NULL
);


ALTER TABLE public.substrapp_dataset OWNER TO substrabac;

--
-- Name: substrapp_model; Type: TABLE; Schema: public; Owner: substrabac
--

CREATE TABLE public.substrapp_model (
    pkhash character varying(64) NOT NULL,
    validated boolean NOT NULL,
    file character varying(500) NOT NULL
);


ALTER TABLE public.substrapp_model OWNER TO substrabac;

--
-- Name: auth_group id; Type: DEFAULT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_group ALTER COLUMN id SET DEFAULT nextval('public.auth_group_id_seq'::regclass);


--
-- Name: auth_group_permissions id; Type: DEFAULT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_group_permissions ALTER COLUMN id SET DEFAULT nextval('public.auth_group_permissions_id_seq'::regclass);


--
-- Name: auth_permission id; Type: DEFAULT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_permission ALTER COLUMN id SET DEFAULT nextval('public.auth_permission_id_seq'::regclass);


--
-- Name: auth_user id; Type: DEFAULT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_user ALTER COLUMN id SET DEFAULT nextval('public.auth_user_id_seq'::regclass);


--
-- Name: auth_user_groups id; Type: DEFAULT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_user_groups ALTER COLUMN id SET DEFAULT nextval('public.auth_user_groups_id_seq'::regclass);


--
-- Name: auth_user_user_permissions id; Type: DEFAULT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_user_user_permissions ALTER COLUMN id SET DEFAULT nextval('public.auth_user_user_permissions_id_seq'::regclass);


--
-- Name: django_admin_log id; Type: DEFAULT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.django_admin_log ALTER COLUMN id SET DEFAULT nextval('public.django_admin_log_id_seq'::regclass);


--
-- Name: django_content_type id; Type: DEFAULT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.django_content_type ALTER COLUMN id SET DEFAULT nextval('public.django_content_type_id_seq'::regclass);


--
-- Name: django_migrations id; Type: DEFAULT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.django_migrations ALTER COLUMN id SET DEFAULT nextval('public.django_migrations_id_seq'::regclass);


--
-- Name: django_site id; Type: DEFAULT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.django_site ALTER COLUMN id SET DEFAULT nextval('public.django_site_id_seq'::regclass);


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can add permission	2	add_permission
5	Can change permission	2	change_permission
6	Can delete permission	2	delete_permission
7	Can add group	3	add_group
8	Can change group	3	change_group
9	Can delete group	3	delete_group
10	Can add user	4	add_user
11	Can change user	4	change_user
12	Can delete user	4	delete_user
13	Can add content type	5	add_contenttype
14	Can change content type	5	change_contenttype
15	Can delete content type	5	delete_contenttype
16	Can add session	6	add_session
17	Can change session	6	change_session
18	Can delete session	6	delete_session
19	Can add site	7	add_site
20	Can change site	7	change_site
21	Can delete site	7	delete_site
22	Can add algo	8	add_algo
23	Can change algo	8	change_algo
24	Can delete algo	8	delete_algo
25	Can add challenge	9	add_challenge
26	Can change challenge	9	change_challenge
27	Can delete challenge	9	delete_challenge
28	Can add data	10	add_data
29	Can change data	10	change_data
30	Can delete data	10	delete_data
31	Can add dataset	11	add_dataset
32	Can change dataset	11	change_dataset
33	Can delete dataset	11	delete_dataset
34	Can add model	12	add_model
35	Can change model	12	change_model
36	Can delete model	12	delete_model
37	Can view log entry	1	view_logentry
38	Can view permission	2	view_permission
39	Can view group	3	view_group
40	Can view user	4	view_user
41	Can view content type	5	view_contenttype
42	Can view session	6	view_session
43	Can view site	7	view_site
44	Can view algo	8	view_algo
45	Can view challenge	9	view_challenge
46	Can view data	10	view_data
47	Can view dataset	11	view_dataset
48	Can view model	12	view_model
\.


--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
\.


--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.auth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	auth	user
5	contenttypes	contenttype
6	sessions	session
7	sites	site
8	substrapp	algo
9	substrapp	challenge
10	substrapp	data
11	substrapp	dataset
12	substrapp	model
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2018-08-29 18:05:11.121702+02
2	auth	0001_initial	2018-08-29 18:05:11.339827+02
3	admin	0001_initial	2018-08-29 18:05:11.409992+02
4	admin	0002_logentry_remove_auto_add	2018-08-29 18:05:11.441996+02
5	contenttypes	0002_remove_content_type_name	2018-08-29 18:05:11.468696+02
6	auth	0002_alter_permission_name_max_length	2018-08-29 18:05:11.476193+02
7	auth	0003_alter_user_email_max_length	2018-08-29 18:05:11.488054+02
8	auth	0004_alter_user_username_opts	2018-08-29 18:05:11.4971+02
9	auth	0005_alter_user_last_login_null	2018-08-29 18:05:11.509746+02
10	auth	0006_require_contenttypes_0002	2018-08-29 18:05:11.513954+02
11	auth	0007_alter_validators_add_error_messages	2018-08-29 18:05:11.540434+02
12	auth	0008_alter_user_username_max_length	2018-08-29 18:05:11.561164+02
13	auth	0009_alter_user_last_name_max_length	2018-08-29 18:05:11.572269+02
14	sessions	0001_initial	2018-08-29 18:05:11.605552+02
15	sites	0001_initial	2018-08-29 18:05:11.629132+02
16	sites	0002_alter_domain_unique	2018-08-29 18:05:11.657023+02
17	substrapp	0001_initial	2018-08-29 18:05:11.761932+02
18	substrapp	0002_auto_20180821_1615	2018-08-29 18:05:11.819214+02
19	admin	0003_logentry_add_action_flag_choices	2018-08-31 15:39:55.425049+02
20	substrapp	0003_auto_20180831_1339	2018-08-31 15:39:55.439014+02
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
\.


--
-- Data for Name: django_site; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.django_site (id, domain, name) FROM stdin;
1	owkin.substrabac:8000	owkin
\.


--
-- Data for Name: substrapp_algo; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.substrapp_algo (pkhash, file, description, validated) FROM stdin;
\.


--
-- Data for Name: substrapp_challenge; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.substrapp_challenge (creation_date, last_modified, pkhash, validated, description, metrics) FROM stdin;
2018-08-31 19:36:58.196+02	2018-08-31 19:37:01.256+02	6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c	t	challenges/6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/description.md	challenges/6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/metrics.py
\.


--
-- Data for Name: substrapp_data; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.substrapp_data (pkhash, validated, file) FROM stdin;
e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1	t	data/e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1/0024900.zip
4b5152871b181d10ee774c10458c064c70710f4ba35938f10c0b7aa51f7dc010	t	data/4b5152871b181d10ee774c10458c064c70710f4ba35938f10c0b7aa51f7dc010/0024701.zip
eed4c6ea09babe7ca6428377fff6e54102ef5cdb0cae593732ddbe3f224217cb	t	data/eed4c6ea09babe7ca6428377fff6e54102ef5cdb0cae593732ddbe3f224217cb/0024316.zip
2d0f943aa81a9cb3fe84b162559ce6aff068ccb04e0cb284733b8f9d7e06517e	t	data/2d0f943aa81a9cb3fe84b162559ce6aff068ccb04e0cb284733b8f9d7e06517e/0024315.zip
93e4b1e040b08cfa8a68b13f9dddb95a6672e8a377378545b2b1254691cfc060	t	data/93e4b1e040b08cfa8a68b13f9dddb95a6672e8a377378545b2b1254691cfc060/0024317.zip
533ee6e7b9d8b247e7e853b24547f57e6ef351852bac0418f13a0666173448f1	t	data/533ee6e7b9d8b247e7e853b24547f57e6ef351852bac0418f13a0666173448f1/0024318.zip
\.


--
-- Data for Name: substrapp_dataset; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.substrapp_dataset (pkhash, name, data_opener, description, validated) FROM stdin;
9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528	ISIC 2019	datasets/9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528/opener.py	datasets/9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528/description.md	t
\.


--
-- Data for Name: substrapp_model; Type: TABLE DATA; Schema: public; Owner: substrabac
--

COPY public.substrapp_model (pkhash, validated, file) FROM stdin;
\.


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: substrabac
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: substrabac
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: substrabac
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 48, true);


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: substrabac
--

SELECT pg_catalog.setval('public.auth_user_groups_id_seq', 1, false);


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: substrabac
--

SELECT pg_catalog.setval('public.auth_user_id_seq', 1, false);


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: substrabac
--

SELECT pg_catalog.setval('public.auth_user_user_permissions_id_seq', 1, false);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: substrabac
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: substrabac
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 12, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: substrabac
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 20, true);


--
-- Name: django_site_id_seq; Type: SEQUENCE SET; Schema: public; Owner: substrabac
--

SELECT pg_catalog.setval('public.django_site_id_seq', 1, true);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_user_id_group_id_94350c0c_uniq; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_group_id_94350c0c_uniq UNIQUE (user_id, group_id);


--
-- Name: auth_user auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_permission_id_14a6b632_uniq; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_permission_id_14a6b632_uniq UNIQUE (user_id, permission_id);


--
-- Name: auth_user auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: django_site django_site_domain_a2e37b91_uniq; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.django_site
    ADD CONSTRAINT django_site_domain_a2e37b91_uniq UNIQUE (domain);


--
-- Name: django_site django_site_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.django_site
    ADD CONSTRAINT django_site_pkey PRIMARY KEY (id);


--
-- Name: substrapp_algo substrapp_algo_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.substrapp_algo
    ADD CONSTRAINT substrapp_algo_pkey PRIMARY KEY (pkhash);


--
-- Name: substrapp_challenge substrapp_challenge_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.substrapp_challenge
    ADD CONSTRAINT substrapp_challenge_pkey PRIMARY KEY (pkhash);


--
-- Name: substrapp_data substrapp_data_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.substrapp_data
    ADD CONSTRAINT substrapp_data_pkey PRIMARY KEY (pkhash);


--
-- Name: substrapp_dataset substrapp_dataset_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.substrapp_dataset
    ADD CONSTRAINT substrapp_dataset_pkey PRIMARY KEY (pkhash);


--
-- Name: substrapp_model substrapp_model_pkey; Type: CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.substrapp_model
    ADD CONSTRAINT substrapp_model_pkey PRIMARY KEY (pkhash);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: auth_user_groups_group_id_97559544; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX auth_user_groups_group_id_97559544 ON public.auth_user_groups USING btree (group_id);


--
-- Name: auth_user_groups_user_id_6a12ed8b; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX auth_user_groups_user_id_6a12ed8b ON public.auth_user_groups USING btree (user_id);


--
-- Name: auth_user_user_permissions_permission_id_1fbb5f2c; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX auth_user_user_permissions_permission_id_1fbb5f2c ON public.auth_user_user_permissions USING btree (permission_id);


--
-- Name: auth_user_user_permissions_user_id_a95ead1b; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX auth_user_user_permissions_user_id_a95ead1b ON public.auth_user_user_permissions USING btree (user_id);


--
-- Name: auth_user_username_6821ab7c_like; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX auth_user_username_6821ab7c_like ON public.auth_user USING btree (username varchar_pattern_ops);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: django_site_domain_a2e37b91_like; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX django_site_domain_a2e37b91_like ON public.django_site USING btree (domain varchar_pattern_ops);


--
-- Name: substrapp_algo_pkhash_650a92a5_like; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX substrapp_algo_pkhash_650a92a5_like ON public.substrapp_algo USING btree (pkhash varchar_pattern_ops);


--
-- Name: substrapp_challenge_pkhash_24c787bd_like; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX substrapp_challenge_pkhash_24c787bd_like ON public.substrapp_challenge USING btree (pkhash varchar_pattern_ops);


--
-- Name: substrapp_data_pkhash_8b8b4ffd_like; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX substrapp_data_pkhash_8b8b4ffd_like ON public.substrapp_data USING btree (pkhash varchar_pattern_ops);


--
-- Name: substrapp_dataset_pkhash_8d7c0be8_like; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX substrapp_dataset_pkhash_8d7c0be8_like ON public.substrapp_dataset USING btree (pkhash varchar_pattern_ops);


--
-- Name: substrapp_model_pkhash_db92e957_like; Type: INDEX; Schema: public; Owner: substrabac
--

CREATE INDEX substrapp_model_pkhash_db92e957_like ON public.substrapp_model USING btree (pkhash varchar_pattern_ops);


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_group_id_97559544_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_user_id_6a12ed8b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: substrabac
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

