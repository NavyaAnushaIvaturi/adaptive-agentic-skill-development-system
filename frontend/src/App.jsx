
import React, { useEffect, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

/* =====================================================
   INITIAL PROFILE
===================================================== */

const initialProfile = {
  mode: "general",
  current_role: "",
  learning_style: "hands-on",
  preferred_difficulty: "beginner",
  time_per_day: 60,
  duration_days: 28,
  career_goal: "",
  interests: "",
  project: "",
  current_skills: "",
  skills_to_learn: "",
  technologies_to_learn: "",
};


/* =====================================================
   APP
===================================================== */

function App() {
  const [token, setToken] = useState(
    localStorage.getItem("access_token") || ""
  );

  const [user, setUser] = useState(null);
  const [screen, setScreen] = useState("loading");
  const [authMode, setAuthMode] = useState("signup");
  const [profile, setProfile] = useState(initialProfile);

  const [learning, setLearning] = useState(null);
  const [progress, setProgress] = useState(null);
  const [quizHistory, setQuizHistory] = useState([]);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);


  /* =====================================================
     RESTORE SESSION
  ===================================================== */

  useEffect(() => {
    restoreSession();
  }, []);


  /* =====================================================
     API REQUEST
  ===================================================== */

  async function apiRequest(path, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    const currentToken =
      token || localStorage.getItem("access_token");

    if (currentToken) {
      headers.Authorization = `Bearer ${currentToken}`;
    }

    const response = await fetch(
      `${API_BASE}${path}`,
      {
        ...options,
        headers,
      }
    );

    let data = null;

    try {
      data = await response.json();
    } catch {
      data = null;
    }

    if (!response.ok) {
      throw new Error(
        data?.detail ||
          data?.message ||
          "Something went wrong."
      );
    }

    return data;
  }


  /* =====================================================
     LOAD QUIZ HISTORY
  ===================================================== */

  async function loadQuizHistory(learningId) {
    if (!learningId) return;

    try {
      const data = await apiRequest(
        `/learning/${learningId}/quiz-history`
      );

      setQuizHistory(data?.attempts || []);
    } catch (err) {
      console.error(
        "Unable to load quiz history:",
        err
      );
    }
  }


  /* =====================================================
     HELPER
  ===================================================== */

  function parseCommaSeparated(value) {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }


  /* =====================================================
     LOAD PROFILE
  ===================================================== */

  function loadProfileFromUser(data) {
    setProfile({
      mode:
        data?.mode ||
        data?.learning_mode ||
        "general",

      current_role:
        data?.current_role || "",

      learning_style:
        data?.learning_style ||
        "hands-on",

      preferred_difficulty:
        data?.preferred_difficulty ||
        "beginner",

      time_per_day:
        data?.time_per_day || 60,

      duration_days:
        data?.duration_days || 28,

      career_goal:
        data?.career_goal || "",

      interests: Array.isArray(data?.interests)
        ? data.interests.join(", ")
        : data?.interests || "",

      project:
        data?.project || "",

      current_skills: Array.isArray(
        data?.current_skills
      )
        ? data.current_skills.join(", ")
        : data?.current_skills || "",

      skills_to_learn: Array.isArray(
        data?.required_skills
      )
        ? data.required_skills.join(", ")
        : data?.required_skills || "",

      technologies_to_learn: Array.isArray(
        data?.required_technologies
      )
        ? data.required_technologies.join(", ")
        : data?.required_technologies || "",
    });
  }


  /* =====================================================
     RESTORE SESSION
  ===================================================== */

  async function restoreSession() {
    const savedToken =
      localStorage.getItem("access_token");

    if (!savedToken) {
      setScreen("welcome");
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE}/auth/me`,
        {
          headers: {
            Authorization:
              `Bearer ${savedToken}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Session expired.");
      }

      const data = await response.json();

      setToken(savedToken);
      setUser(data);

      loadProfileFromUser(data);

      // Try to restore the latest learning session
      try {
        const sessionRes = await fetch(
          `${API_BASE}/learning/my-session`,
          {
            headers: {
              Authorization: `Bearer ${savedToken}`,
            },
          }
        );
        if (sessionRes.ok) {
          const sessionData = await sessionRes.json();
          if (sessionData?.session) {
            const sess = sessionData.session;
            setLearning(sess);

            const status = sess.status;
            if (status === "TOPIC_ASSESSMENT") {
              setScreen("quiz");
            } else if (status === "COMPLETED") {
              setScreen("progress");
            } else if (
              status === "DAILY_ACTIVITY" ||
              status === "REMEDIAL_ACTIVITY"
            ) {
              if (sess.roadmap_approved) {
                setScreen("activity");
              } else {
                setScreen("roadmap");
              }
            } else if (
              status === "PENDING_APPROVAL" ||
              status === "ROADMAP_GENERATED"
            ) {
              setScreen("roadmap");
            } else {
              setScreen("profile");
            }
            return;
          }
        }
      } catch {
        // No active session — go to profile
      }

      setScreen("profile");
    } catch {
      localStorage.removeItem("access_token");

      setToken("");
      setUser(null);
      setLearning(null);
      setProgress(null);
      setQuizHistory([]);
      setProfile(initialProfile);

      setScreen("welcome");
    }
  }


  /* =====================================================
     AUTH
  ===================================================== */

  async function handleSignup(form) {
    setError("");
    setLoading(true);

    try {
      if (
        form.password !==
        form.confirm_password
      ) {
        throw new Error(
          "Passwords do not match."
        );
      }

      const data = await apiRequest(
        "/auth/signup",
        {
          method: "POST",
          body: JSON.stringify({
            full_name:
              form.full_name,
            email:
              form.email,
            password:
              form.password,
          }),
        }
      );

      const newToken =
        data.access_token ||
        data.token;

      if (!newToken) {
        throw new Error(
          "Account created but no access token was returned."
        );
      }

      localStorage.setItem(
        "access_token",
        newToken
      );

      setToken(newToken);

      setUser(
        data.user || data
      );

      setProfile(initialProfile);

      setScreen("profile");
    } catch (err) {
      setError(
        err.message ||
          "Unable to create account."
      );
    } finally {
      setLoading(false);
    }
  }


  async function handleLogin(form) {
    setError("");
    setLoading(true);

    try {
      const data =
        await apiRequest(
          "/auth/login",
          {
            method: "POST",
            body: JSON.stringify({
              email:
                form.email,
              password:
                form.password,
            }),
          }
        );

      const newToken =
        data.access_token ||
        data.token;

      if (!newToken) {
        throw new Error(
          "Login succeeded but no access token was returned."
        );
      }

      localStorage.setItem(
        "access_token",
        newToken
      );

      setToken(newToken);

      const me = await fetch(
        `${API_BASE}/auth/me`,
        {
          headers: {
            Authorization:
              `Bearer ${newToken}`,
          },
        }
      );

      if (!me.ok) {
        throw new Error(
          "Unable to load your profile."
        );
      }

      const userData =
        await me.json();

      setUser(userData);

      loadProfileFromUser(userData);

      setScreen("profile");
    } catch (err) {
      setError(
        err.message ||
          "Unable to sign in."
      );
    } finally {
      setLoading(false);
    }
  }


  async function logout() {
    try {
      const currentToken =
        token ||
        localStorage.getItem(
          "access_token"
        );

      if (currentToken) {
        await fetch(
          `${API_BASE}/auth/logout`,
          {
            method: "POST",
            headers: {
              Authorization:
                `Bearer ${currentToken}`,
            },
          }
        );
      }
    } catch {
      // Continue logout.
    }

    localStorage.removeItem(
      "access_token"
    );

    setToken("");
    setUser(null);
    setLearning(null);
    setProgress(null);
    setQuizHistory([]);
    setProfile(initialProfile);
    setError("");
    setScreen("welcome");
  }


  /* =====================================================
     PROFILE
  ===================================================== */

  function updateProfile(field, value) {
    setProfile(
      (previous) => ({
        ...previous,
        [field]: value,
      })
    );
  }


  /* =====================================================
     START LEARNING
  ===================================================== */

  async function startLearning() {
    setError("");

    if (!profile.mode) {
      setError(
        "Please select a learning mode."
      );
      return;
    }

    if (
      !profile.current_role.trim()
    ) {
      setError(
        "Current role is required."
      );
      return;
    }

    if (!profile.learning_style) {
      setError(
        "Learning preference is required."
      );
      return;
    }

    if (!profile.preferred_difficulty) {
      setError(
        "Difficulty is required."
      );
      return;
    }

    if (
      !profile.time_per_day ||
      Number(profile.time_per_day) < 1
    ) {
      setError(
        "Minutes per day must be at least 1."
      );
      return;
    }

    if (
      !profile.duration_days ||
      Number(profile.duration_days) < 1
    ) {
      setError(
        "Duration must be at least 1 day."
      );
      return;
    }


    /* GENERAL MODE */

    if (
      profile.mode === "general" &&
      !profile.career_goal.trim()
    ) {
      setError(
        "Career goal is required."
      );
      return;
    }


    /* PROJECT MODE */

    if (
      profile.mode ===
      "project-oriented"
    ) {
      if (
        !profile.project.trim()
      ) {
        setError(
          "Project is required for Project Oriented mode."
        );
        return;
      }

      const skillsToLearn =
        parseCommaSeparated(
          profile.skills_to_learn
        );

      const technologiesToLearn =
        parseCommaSeparated(
          profile.technologies_to_learn
        );

      if (
        skillsToLearn.length === 0 &&
        technologiesToLearn.length === 0
      ) {
        setError(
          "Please enter at least one skill or technology you want to learn."
        );
        return;
      }
    }


    setLoading(true);

    try {
      const interests =
        parseCommaSeparated(
          profile.interests
        );

      const currentSkills =
        parseCommaSeparated(
          profile.current_skills
        );

      const skillsToLearn =
        parseCommaSeparated(
          profile.skills_to_learn
        );

      const technologiesToLearn =
        parseCommaSeparated(
          profile.technologies_to_learn
        );


      const payload = {
        mode:
          profile.mode === "project-oriented"
            ? "project"
            : profile.mode,

        goal:
          profile.career_goal.trim(),

        current_level:
          profile.preferred_difficulty ||
          "beginner",

        time_per_day:
          Number(
            profile.time_per_day
          ),

        duration_days:
          Number(
            profile.duration_days
          ),

        preference:
          profile.learning_style,

        role:
          profile.current_role.trim(),

        project:
          profile.mode ===
          "project-oriented"
            ? profile.project.trim()
            : "",

        current_skills:
          profile.mode ===
          "project-oriented"
            ? currentSkills
            : [],

        required_skills:
          profile.mode ===
          "project-oriented"
            ? skillsToLearn
            : interests,

        required_technologies:
          profile.mode ===
          "project-oriented"
            ? technologiesToLearn
            : [],

        deadline: "",
      };


      const data =
        await apiRequest(
          "/learning/start",
          {
            method: "POST",
            body:
              JSON.stringify(
                payload
              ),
          }
        );


      setLearning(data);
      setScreen("roadmap");

    } catch (err) {
      setError(
        err.message ||
          "Unable to create your learning roadmap."
      );
    } finally {
      setLoading(false);
    }
  }


  /* =====================================================
     ROADMAP APPROVAL
  ===================================================== */

  async function approveRoadmap() {
    if (!learning?.learning_id) {
      return;
    }

    setError("");
    setLoading(true);

    try {
      const data =
        await apiRequest(
          `/learning/${learning.learning_id}/approve`,
          {
            method: "POST",
            body:
              JSON.stringify({
                approved: true,
              }),
          }
        );

      setLearning(data);

      if (data?.current_activity) {
        setScreen("activity");
      } else {
        setScreen("roadmap");
      }
    } catch (err) {
      setError(
        err.message ||
          "Unable to start the roadmap."
      );
    } finally {
      setLoading(false);
    }
  }


  /* =====================================================
     DASHBOARD
  ===================================================== */

  async function openDashboard() {
    if (!learning?.learning_id) {
      setScreen("profile");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const data =
        await apiRequest(
          `/learning/${learning.learning_id}/progress`
        );

      setProgress(data);

      /*
       * Keep the main learning object synchronized
       * with the backend dashboard state.
       */
      setLearning((previous) => ({
        ...(previous || {}),
        ...data,
      }));

      await loadQuizHistory(
        learning.learning_id
      );

      setScreen("progress");
    } catch (err) {
      setError(
        err.message ||
          "Unable to load dashboard."
      );
    } finally {
      setLoading(false);
    }
  }


  /* =====================================================
     CONTINUE LEARNING
  ===================================================== */

  async function continueLearning() {
    if (!learning?.learning_id) {
      setScreen("profile");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const data =
        await apiRequest(
          `/learning/${learning.learning_id}/progress`
        );

      setProgress(data);

      setLearning((previous) => ({
        ...(previous || {}),
        ...data,
      }));

      /*
       * If the backend has already moved to the
       * next week, directly open its activity.
       */
      if (
        data?.status ===
        "TOPIC_ASSESSMENT"
      ) {
        setScreen("quiz");
        return;
      }

      if (
        data?.status ===
        "COMPLETED"
      ) {
        setScreen("progress");
        return;
      }

      if (data?.current_activity) {
        setScreen("activity");
        return;
      }

      setScreen("roadmap");

    } catch (err) {
      setError(
        err.message ||
          "Unable to continue learning."
      );
    } finally {
      setLoading(false);
    }
  }


  /* =====================================================
     ACTIVITY
  ===================================================== */

  async function completeActivity(
    completed
  ) {
    const activity =
      learning?.current_activity;

    if (
      !learning?.learning_id ||
      !activity?.activity_id
    ) {
      return;
    }

    setError("");
    setLoading(true);

    try {
      const data =
        await apiRequest(
          `/learning/${learning.learning_id}/activities/${activity.activity_id}/complete`,
          {
            method: "POST",
            body:
              JSON.stringify({
                completed,
              }),
          }
        );

      setLearning(data);

      if (data?.status === "TOPIC_ASSESSMENT") {
        // Week ended (completed or missed last day) → quiz
        setScreen("quiz");
      } else if (data?.status === "COMPLETED") {
        setScreen("progress");
      } else {
        // Next day (with or without missed previous day shown)
        setScreen("activity");
      }

    } catch (err) {
      setError(
        err.message ||
          "Unable to update the activity."
      );
    } finally {
      setLoading(false);
    }
  }


  /* =====================================================
     QUIZ
  ===================================================== */

  async function submitQuiz(answers) {
    if (!learning?.learning_id) {
      return;
    }

    setError("");
    setLoading(true);

    try {
      const data =
        await apiRequest(
          `/learning/${learning.learning_id}/quiz`,
          {
            method: "POST",
            body:
              JSON.stringify({
                answers,
              }),
          }
        );

      /*
       * Backend returns the complete updated
       * learning state after evaluation.
       */
      setLearning(data);

      await loadQuizHistory(
        data?.learning_id ||
          learning.learning_id
      );

      /*
       * IMPORTANT:
       * Do not expect WEEKLY_FEEDBACK.
       *
       * Your backend is designed so that:
       *
       * 100% -> next week
       * below 100% -> remedial activity
       */
      setScreen("result");

    } catch (err) {
      setError(
        err.message ||
          "Unable to submit the quiz."
      );
    } finally {
      setLoading(false);
    }
  }


  /* =====================================================
     OPEN NEXT ACTIVITY / NEXT WEEK
  ===================================================== */

  async function openNextActivity() {
    if (!learning?.learning_id) {
      return;
    }

    setError("");
    setLoading(true);

    try {
      /*
       * Always ask backend for the latest state.
       * This is important after a 100% quiz because
       * the backend may already have changed:
       *
       * current_week
       * current_day
       * current_topic
       * current_activity
       */
      const latest =
        await apiRequest(
          `/learning/${learning.learning_id}/progress`
        );

      setProgress(latest);

      setLearning((previous) => ({
        ...(previous || {}),
        ...latest,
      }));

      if (
        latest?.status ===
        "TOPIC_ASSESSMENT"
      ) {
        setScreen("quiz");
        return;
      }

      if (
        latest?.status ===
        "COMPLETED"
      ) {
        setScreen("progress");
        return;
      }

      if (latest?.current_activity) {
        setScreen("activity");
        return;
      }

      setScreen("progress");

    } catch (err) {
      setError(
        err.message ||
          "Unable to open the next activity."
      );
    } finally {
      setLoading(false);
    }
  }


  /* =====================================================
     PROFILE NAVIGATION
  ===================================================== */

  function openProfile() {
    setError("");
    setScreen("profile");
  }


  /* =====================================================
     LOADING
  ===================================================== */

  if (screen === "loading") {
    return (
      <div className="app-loading">
        <div className="loading-spinner" />

        <span>
          Loading your learning space...
        </span>
      </div>
    );
  }


  /* =====================================================
     MAIN UI
  ===================================================== */

  return (
    <div className="app-shell">

      {screen !== "welcome" &&
        screen !== "auth" && (
          <TopBar
            onDashboard={
              openDashboard
            }
            onProfile={
              openProfile
            }
            onLogout={
              logout
            }
          />
        )}

      <main className="app-content">

        {error && (
          <div className="error-banner">
            <span>!</span>
            {error}
          </div>
        )}


        {screen === "welcome" && (
          <WelcomeScreen
            onGetStarted={() => {
              setError("");
              setAuthMode("signup");
              setScreen("auth");
            }}
            onSignIn={() => {
              setError("");
              setAuthMode("login");
              setScreen("auth");
            }}
          />
        )}


        {screen === "auth" && (
          <AuthScreen
            mode={authMode}
            setMode={setAuthMode}
            onSignup={
              handleSignup
            }
            onLogin={
              handleLogin
            }
            loading={loading}
          />
        )}


        {screen === "profile" && (
          <LearningProfile
            profile={profile}
            updateProfile={
              updateProfile
            }
            onStart={
              startLearning
            }
            loading={loading}
          />
        )}


        {screen === "roadmap" && (
          <RoadmapScreen
            learning={learning}
            onApprove={
              approveRoadmap
            }
            loading={loading}
          />
        )}


        {screen === "activity" && (
          <ActivityScreen
            learning={learning}
            onComplete={
              completeActivity
            }
            onDashboard={
              openDashboard
            }
            loading={loading}
          />
        )}


        {screen === "quiz" && (
          <QuizScreen
            learning={learning}
            onSubmit={
              submitQuiz
            }
            onDashboard={
              openDashboard
            }
            loading={loading}
          />
        )}


        {screen === "result" && (
          <ResultScreen
            learning={learning}
            onDashboard={
              openDashboard
            }
            onActivity={
              openNextActivity
            }
          />
        )}


        {screen === "progress" && (
          <ProgressScreen
            progress={progress}
            onContinue={
              continueLearning
            }
            onProfile={
              openProfile
            }
          />
        )}

      </main>
    </div>
  );
}


/* =====================================================
   WELCOME
===================================================== */

function WelcomeScreen({
  onGetStarted,
  onSignIn,
}) {
  return (
    <section className="welcome-page">

      <div className="welcome-content">

        <div className="welcome-left">

          <div className="welcome-badge">
            ADAPTIVE LEARNING PLATFORM
          </div>

          <h1 className="welcome-title">
            Learn smarter.
            <br />
            Grow with confidence.
          </h1>

          <p className="welcome-description">
            A personalized learning
            experience that adapts to
            your goals, current level,
            learning preference, and
            available time.
          </p>

          <div className="welcome-actions">

            <button
              type="button"
              className="welcome-primary"
              onClick={
                onGetStarted
              }
            >
              Get Started
              <span>→</span>
            </button>

            <button
              type="button"
              className="welcome-secondary"
              onClick={
                onSignIn
              }
            >
              Sign in
            </button>

          </div>

          <div className="welcome-features">

            <WelcomeFeature
              number="01"
              title="Personalized"
              text="Built around your goals"
            />

            <WelcomeFeature
              number="02"
              title="Adaptive"
              text="Adjusts to your progress"
            />

            <WelcomeFeature
              number="03"
              title="Practical"
              text="Learn through real tasks"
            />

          </div>

        </div>


        <div className="welcome-right">

          <div className="learning-preview">

            <div className="preview-header">

              <div>

                <span>
                  YOUR LEARNING PATH
                </span>

                <h3>
                  Personalized progress
                </h3>

              </div>

              <div className="preview-progress">
                72%
              </div>

            </div>

            <div className="preview-line">
              <div className="preview-line-fill" />
            </div>

            <div className="preview-days">

              <PreviewDay
                completed
                day="1"
                title="Foundations"
              />

              <PreviewDay
                completed
                day="2"
                title="Core concepts"
              />

              <PreviewDay
                active
                day="3"
                title="Practical learning"
              />

              <PreviewDay
                day="4"
                title="Next topic"
              />

            </div>

            <div className="preview-footer">

              <span>
                Today's focus
              </span>

              <strong>
                Learn. Practice. Improve.
              </strong>

            </div>

          </div>

        </div>

      </div>

    </section>
  );
}


function WelcomeFeature({
  number,
  title,
  text,
}) {
  return (
    <div className="welcome-feature">

      <div className="feature-icon">
        {number}
      </div>

      <div>

        <strong>
          {title}
        </strong>

        <span>
          {text}
        </span>

      </div>

    </div>
  );
}


function PreviewDay({
  completed,
  active,
  day,
  title,
}) {
  return (
    <div
      className={
        active
          ? "preview-day active"
          : completed
          ? "preview-day completed"
          : "preview-day"
      }
    >

      <span>
        {completed ? "✓" : day}
      </span>

      <div>

        <strong>
          Day {day}
        </strong>

        <small>
          {title}
        </small>

      </div>

    </div>
  );
}


/* =====================================================
   TOP BAR
===================================================== */

function TopBar({
  onDashboard,
  onProfile,
  onLogout,
}) {
  return (
    <header className="topbar">

      <div className="topbar-brand">

        <div className="brand-mark">
          A
        </div>

        <strong>
          Adaptive Learning
        </strong>

      </div>


      <div className="topbar-actions">

        <button
          type="button"
          className="topbar-button"
          onClick={
            onDashboard
          }
        >
          Dashboard
        </button>

        <button
          type="button"
          className="topbar-button"
          onClick={
            onProfile
          }
        >
          Profile
        </button>

        <button
          type="button"
          className="topbar-button logout-button"
          onClick={
            onLogout
          }
        >
          Logout
        </button>

      </div>

    </header>
  );
}


/* =====================================================
   AUTH
===================================================== */

function AuthScreen({
  mode,
  setMode,
  onSignup,
  onLogin,
  loading,
}) {
  return (
    <section className="auth-page">

      <div className="auth-card">

        {mode === "signup" ? (
          <SignupForm
            onSubmit={
              onSignup
            }
            loading={
              loading
            }
            onLogin={() =>
              setMode("login")
            }
          />
        ) : (
          <LoginForm
            onSubmit={
              onLogin
            }
            loading={
              loading
            }
            onSignup={() =>
              setMode("signup")
            }
          />
        )}

      </div>

    </section>
  );
}


/* =====================================================
   SIGNUP
===================================================== */

function SignupForm({
  onSubmit,
  loading,
  onLogin,
}) {
  const [form, setForm] =
    useState({
      full_name: "",
      email: "",
      password: "",
      confirm_password: "",
    });

  function update(
    field,
    value
  ) {
    setForm(
      (previous) => ({
        ...previous,
        [field]: value,
      })
    );
  }

  function submit(event) {
    event.preventDefault();
    onSubmit(form);
  }

  return (
    <form
      className="form-card"
      onSubmit={submit}
    >

      <div className="form-header">

        <span className="eyebrow">
          CREATE ACCOUNT
        </span>

        <h1>
          Create your account
        </h1>

        <p>
          Create your account
          first. Your learning
          information is collected
          separately in your profile.
        </p>

      </div>


      <div className="form-grid">

        <Field
          label="Name"
          required
          value={
            form.full_name
          }
          onChange={(value) =>
            update(
              "full_name",
              value
            )
          }
          placeholder="Your name"
        />

        <Field
          label="Email"
          required
          type="email"
          value={
            form.email
          }
          onChange={(value) =>
            update(
              "email",
              value
            )
          }
          placeholder="you@example.com"
        />

        <Field
          label="Password"
          required
          type="password"
          value={
            form.password
          }
          onChange={(value) =>
            update(
              "password",
              value
            )
          }
          placeholder="Create a password"
        />

        <Field
          label="Confirm password"
          required
          type="password"
          value={
            form.confirm_password
          }
          onChange={(value) =>
            update(
              "confirm_password",
              value
            )
          }
          placeholder="Confirm password"
        />

      </div>


      <button
        className="primary-button full-width"
        type="submit"
        disabled={loading}
      >
        {loading
          ? "Creating account..."
          : "Create Account →"}
      </button>


      <div className="auth-switch">

        Already have an account?{" "}

        <button
          type="button"
          onClick={
            onLogin
          }
        >
          Sign in
        </button>

      </div>

    </form>
  );
}


/* =====================================================
   LOGIN
===================================================== */

function LoginForm({
  onSubmit,
  loading,
  onSignup,
}) {
  const [form, setForm] =
    useState({
      email: "",
      password: "",
    });

  function submit(event) {
    event.preventDefault();
    onSubmit(form);
  }

  return (
    <form
      className="form-card"
      onSubmit={submit}
    >

      <div className="form-header">

        <span className="eyebrow">
          SIGN IN
        </span>

        <h1>
          Welcome back
        </h1>

        <p>
          Sign in to continue
          your adaptive learning
          journey.
        </p>

      </div>


      <div className="form-grid">

        <Field
          label="Email"
          required
          type="email"
          value={
            form.email
          }
          onChange={(value) =>
            setForm({
              ...form,
              email: value,
            })
          }
          placeholder="you@example.com"
        />

        <Field
          label="Password"
          required
          type="password"
          value={
            form.password
          }
          onChange={(value) =>
            setForm({
              ...form,
              password: value,
            })
          }
          placeholder="Your password"
        />

      </div>


      <button
        className="primary-button full-width"
        type="submit"
        disabled={loading}
      >
        {loading
          ? "Signing in..."
          : "Sign In →"}
      </button>


      <div className="auth-switch">

        Don't have an account?{" "}

        <button
          type="button"
          onClick={
            onSignup
          }
        >
          Create account
        </button>

      </div>

    </form>
  );
}


/* =====================================================
   LEARNING PROFILE
===================================================== */

function LearningProfile({
  profile,
  updateProfile,
  onStart,
  loading,
}) {
  function submit(event) {
    event.preventDefault();
    onStart();
  }

  const isProjectMode =
    profile.mode ===
    "project-oriented";

  return (
    <section className="page-section">

      <div className="page-heading">

        <span className="eyebrow">
          LEARNING PROFILE
        </span>

        <h1>
          Tell us how you want to learn
        </h1>

        <p>
          Configure the information
          needed to create your
          personalized learning path.
        </p>

      </div>


      <form
        className="large-form-card"
        onSubmit={submit}
      >

        <div className="form-section">

          <h2>
            Learning setup
          </h2>


          <div className="field mode-field">

            <span className="field-label">
              Learning mode
              <span className="required-mark">
                *
              </span>
            </span>


            <div className="learning-mode-options">

              <button
                type="button"
                className={
                  profile.mode === "general"
                    ? "learning-mode-card selected"
                    : "learning-mode-card"
                }
                onClick={() =>
                  updateProfile(
                    "mode",
                    "general"
                  )
                }
              >

                <strong>
                  General Learning
                </strong>

                <span>
                  Learn concepts step by
                  step based on your goals,
                  level, and learning
                  preferences.
                </span>

              </button>


              <button
                type="button"
                className={
                  profile.mode ===
                  "project-oriented"
                    ? "learning-mode-card selected"
                    : "learning-mode-card"
                }
                onClick={() =>
                  updateProfile(
                    "mode",
                    "project-oriented"
                  )
                }
              >

                <strong>
                  Project Oriented
                </strong>

                <span>
                  Learn the skills and
                  technologies needed for
                  your project.
                </span>

              </button>

            </div>

          </div>


          <div className="form-grid two-columns">

            <Field
              label="Current role"
              required
              value={
                profile.current_role
              }
              onChange={(value) =>
                updateProfile(
                  "current_role",
                  value
                )
              }
              placeholder="e.g. Student, Developer, Data Analyst"
            />


            <SelectField
              label="Learning preference"
              required
              value={
                profile.learning_style
              }
              onChange={(value) =>
                updateProfile(
                  "learning_style",
                  value
                )
              }
              options={[
                [
                  "hands-on",
                  "Hands-on practice",
                ],
                [
                  "visual",
                  "Visual learning",
                ],
                [
                  "reading",
                  "Reading and explanation",
                ],
                [
                  "mixed",
                  "Mixed learning",
                ],
              ]}
            />


            <SelectField
              label="Difficulty"
              required
              value={
                profile.preferred_difficulty
              }
              onChange={(value) =>
                updateProfile(
                  "preferred_difficulty",
                  value
                )
              }
              options={[
                [
                  "beginner",
                  "Beginner",
                ],
                [
                  "intermediate",
                  "Intermediate",
                ],
                [
                  "advanced",
                  "Advanced",
                ],
              ]}
            />


            <NumberField
              label="Minutes per day"
              required
              min={1}
              value={
                profile.time_per_day
              }
              onChange={(value) =>
                updateProfile(
                  "time_per_day",
                  value
                )
              }
            />


            <NumberField
              label="Duration in days"
              required
              min={1}
              value={
                profile.duration_days
              }
              onChange={(value) =>
                updateProfile(
                  "duration_days",
                  value
                )
              }
            />

          </div>

        </div>


        {isProjectMode && (
          <>
            <div className="form-divider" />

            <div className="form-section">

              <h2>
                Project learning setup
              </h2>

              <p className="section-description">
                Tell us what you already know
                and what you want to learn.
                The project provides context,
                while the roadmap focuses on
                the skills you need.
              </p>


              <Field
                label="Project"
                required
                value={
                  profile.project
                }
                onChange={(value) =>
                  updateProfile(
                    "project",
                    value
                  )
                }
                placeholder="e.g. Disease Prediction Website"
              />


              <div className="form-grid two-columns">

                <label className="field">

                  <span className="field-label">

                    Current skills

                    <span className="optional-mark">
                      Optional
                    </span>

                  </span>

                  <input
                    className="text-input"
                    type="text"
                    value={
                      profile.current_skills
                    }
                    onChange={(event) =>
                      updateProfile(
                        "current_skills",
                        event.target.value
                      )
                    }
                    placeholder="e.g. Python, HTML, CSS"
                  />

                  <span className="field-help">
                    Enter the skills you
                    already know, separated
                    by commas.
                  </span>

                </label>


                <label className="field">

                  <span className="field-label">

                    Skills to learn

                    <span className="required-mark">
                      *
                    </span>

                  </span>

                  <input
                    className="text-input"
                    type="text"
                    value={
                      profile.skills_to_learn
                    }
                    onChange={(event) =>
                      updateProfile(
                        "skills_to_learn",
                        event.target.value
                      )
                    }
                    placeholder="e.g. Machine Learning, Computer Vision"
                    required={
                      isProjectMode &&
                      !profile.technologies_to_learn.trim()
                    }
                  />

                  <span className="field-help">
                    Enter the skills you want
                    the roadmap to teach.
                  </span>

                </label>


                <label className="field">

                  <span className="field-label">

                    Technologies to learn

                    <span className="optional-mark">
                      Optional
                    </span>

                  </span>

                  <input
                    className="text-input"
                    type="text"
                    value={
                      profile.technologies_to_learn
                    }
                    onChange={(event) =>
                      updateProfile(
                        "technologies_to_learn",
                        event.target.value
                      )
                    }
                    placeholder="e.g. FastAPI, React, Docker"
                  />

                  <span className="field-help">
                    Add technologies that are
                    important for the project.
                  </span>

                </label>

              </div>

            </div>
          </>
        )}


        <div className="form-divider" />


        <div className="form-section">

          <h2>

            Career goal

            {profile.mode === "general" && (
              <span className="required-mark">
                *
              </span>
            )}

            {profile.mode === "project-oriented" && (
              <span className="optional-mark">
                Optional
              </span>
            )}

          </h2>

          <p className="section-description">
            {profile.mode === "project-oriented"
              ? "Optional in Project Oriented mode. Your project and learning requirements drive the roadmap."
              : "What do you want to achieve through this learning plan?"}
          </p>

          <textarea
            className="text-area"
            required={
              profile.mode === "general"
            }
            value={
              profile.career_goal
            }
            onChange={(event) =>
              updateProfile(
                "career_goal",
                event.target.value
              )
            }
            placeholder={
              profile.mode === "project-oriented"
                ? "Optional: e.g. Become confident in AI application development"
                : "e.g. Become confident in Python development and build real projects"
            }
            rows={4}
          />

        </div>


        {profile.mode === "general" && (
          <div className="form-section">

            <h2>

              Interests

              <span className="optional-mark">
                Optional
              </span>

            </h2>

            <p className="section-description">
              Add technologies or topics
              you want included.
            </p>

            <input
              className="text-input"
              value={
                profile.interests
              }
              onChange={(event) =>
                updateProfile(
                  "interests",
                  event.target.value
                )
              }
              placeholder="e.g. Python, FastAPI, machine learning"
            />

          </div>
        )}


        <div className="profile-actions">

          <button
            type="submit"
            className="primary-button"
            disabled={loading}
          >
            {loading
              ? "Creating your roadmap..."
              : "Save & Start Learning →"}
          </button>

        </div>

      </form>

    </section>
  );
}


/* =====================================================
   ROADMAP
===================================================== */

function RoadmapScreen({
  learning,
  onApprove,
  loading,
}) {
  const roadmap =
    learning?.roadmap || {};

  const weeks =
    roadmap?.weeks || [];

  return (
    <section className="page-section">

      <div className="page-heading">

        <span className="eyebrow">
          YOUR ROADMAP
        </span>

        <h1>
          Your personalized learning path
        </h1>

        <p>
          Review the roadmap created
          from your learning profile.
        </p>

      </div>


      <div className="roadmap-summary">

        <SummaryItem
          label="Goal"
          value={
            learning?.goal ||
            "Learning goal"
          }
        />

        <SummaryItem
          label="Current level"
          value={
            learning?.current_level ||
            "Beginner"
          }
        />

        <SummaryItem
          label="Daily time"
          value={
            learning?.context
              ?.time_per_day
              ? `${learning.context.time_per_day} min`
              : "Configured"
          }
        />

      </div>


      {weeks.length === 0 ? (
        <div className="empty-card">

          <h2>
            Roadmap generated
          </h2>

          <p>
            Your roadmap is ready.
            Continue to begin learning.
          </p>

        </div>
      ) : (
        <div className="roadmap-list">

          {weeks.map(
            (week, index) => (
              <div
                className="roadmap-week"
                key={
                  week.week ||
                  index
                }
              >

                <div className="week-number">
                  Week{" "}
                  {week.week ||
                    index + 1}
                </div>

                <div className="week-content">

                  <h2>
                    {week.title ||
                      week.topic ||
                      `Week ${
                        index + 1
                      }`}
                  </h2>

                  {week.description && (
                    <p>
                      {
                        week.description
                      }
                    </p>
                  )}


                  {Array.isArray(
                    week.days
                  ) &&
                    week.days.length >
                      0 && (
                      <div className="roadmap-days">

                        {week.days.map(
                          (
                            day,
                            dayIndex
                          ) => (
                            <div
                              className="roadmap-day"
                              key={
                                dayIndex
                              }
                            >

                              <strong>
                                Day{" "}
                                {day.day ||
                                  dayIndex +
                                    1}
                              </strong>

                              <span>
                                {typeof day ===
                                "string"
                                  ? day
                                  : day.focus ||
                                    day.title ||
                                    day.description ||
                                    "Learning activity"}
                              </span>

                            </div>
                          )
                        )}

                      </div>
                    )}

                </div>

              </div>
            )
          )}

        </div>
      )}


      <div className="roadmap-actions">

        <button
          type="button"
          className="primary-button"
          onClick={
            onApprove
          }
          disabled={loading}
        >
          {loading
            ? "Starting..."
            : "Approve & Start Learning →"}
        </button>

      </div>

    </section>
  );
}


/* =====================================================
   ACTIVITY
===================================================== */

function ActivityScreen({
  learning,
  onComplete,
  onDashboard,
  loading,
}) {
  const activity =
    learning?.current_activity;

  const previous =
    learning?.previous_activity;


  if (!activity) {
    return (
      <section className="page-section">

        <div className="empty-card">

          <h2>
            No activity available
          </h2>

          <p>
            Your next learning activity
            is not available yet.
          </p>

          <button
            type="button"
            className="primary-button"
            onClick={
              onDashboard
            }
          >
            Dashboard
          </button>

        </div>

      </section>
    );
  }


  const resources = (
    activity.resources || []
  ).slice(0, 2);


  return (
    <section className="activity-page">

      <div className="activity-topbar">

        <div>

          <span className="eyebrow">
            WEEK {activity.week} · DAY {activity.day}
          </span>

          <h1>
            {activity.topic}
          </h1>

          {(activity.base_focus || activity.focus) && (
            <p className="activity-subtitle">
              {activity.base_focus || activity.focus}
            </p>
          )}

        </div>


        <button
          type="button"
          className="secondary-button"
          onClick={
            onDashboard
          }
        >
          Dashboard
        </button>

      </div>


      {previous && (
        <section className="previous-day-section">

          <div className="missed-day-label">
            ⚠ Missed from yesterday — Day {previous.day}
          </div>

          <h2>
            {previous.title || previous.topic}
          </h2>

          {(previous.base_focus || previous.focus) && (
            <p className="previous-focus">
              <strong>Focus: </strong>
              {previous.base_focus || previous.focus}
            </p>
          )}

          {previous.description && (
            <p>
              {previous.description}
            </p>
          )}

          {previous.learning_content && (
            <div className="previous-content">
              <strong>What you missed:</strong>
              <p>{previous.learning_content}</p>
            </div>
          )}

          {previous.objectives?.length > 0 && (
            <div className="compact-takeaways">
              <strong>Learning objectives</strong>
              <ul>
                {previous.objectives.slice(0, 3).map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {previous.key_takeaways?.length > 0 && (
            <div className="compact-takeaways">
              <strong>Key takeaways</strong>
              <ul>
                {previous.key_takeaways.slice(0, 3).map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          )}

        </section>
      )}


      <section className="today-section">

        <div className="activity-meta">

          <span>
            Week {activity.week}
          </span>

          <span>
            Day {activity.day}
          </span>

          {activity.remedial && (
            <span>
              Review
            </span>
          )}

        </div>


        <h2>
          {activity.title ||
            activity.topic}
        </h2>


        <div className="focus-block">

          <span className="section-label">
            TODAY'S FOCUS
          </span>

          <p>
            {activity.base_focus ||
              activity.focus ||
              activity.topic}
          </p>

        </div>


        {activity.objectives
          ?.length > 0 && (
          <ContentSection
            title="What you'll learn"
            items={
              activity.objectives
            }
          />
        )}


        {activity.learning_content && (
          <ContentSection
            title="Explanation"
            text={
              activity.learning_content
            }
          />
        )}


        {activity.examples
          ?.length > 0 && (
          <ContentSection
            title="Example"
            items={
              activity.examples
            }
          />
        )}


        {activity.steps
          ?.length > 0 && (
          <ContentSection
            title="Steps"
            ordered
            items={
              activity.steps
            }
          />
        )}


        {activity.practical_task && (
          <ContentSection
            title="Practical task"
            text={
              activity.practical_task
            }
          />
        )}


        {activity.key_takeaways
          ?.length > 0 && (
          <ContentSection
            title="Key takeaways"
            items={
              activity.key_takeaways
            }
          />
        )}


        {resources.length > 0 && (
          <section className="content-section">

            <div className="section-label">
              RESOURCES
            </div>

            <div className="resource-list">

              {resources.map(
                (
                  resource,
                  index
                ) => {
                  const url =
                    resource.url ||
                    resource.link;

                  const title =
                    resource.title ||
                    resource.name ||
                    `Learning resource ${
                      index + 1
                    }`;

                  return (
                    <div
                      className="resource-item"
                      key={
                        index
                      }
                    >

                      {url ? (
                        <a
                          href={url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {title}
                        </a>
                      ) : (
                        <span>
                          {title}
                        </span>
                      )}

                    </div>
                  );
                }
              )}

            </div>

          </section>
        )}


        <div className="activity-status">

          <span className="section-label">
            STATUS
          </span>

          <strong>
            {activity.status ||
              "PENDING"}
          </strong>

        </div>


        <div className="activity-actions">

          <button
            type="button"
            className="secondary-button"
            onClick={() =>
              onComplete(false)
            }
            disabled={loading}
          >
            Not Done
          </button>

          <button
            type="button"
            className="primary-button"
            onClick={() =>
              onComplete(true)
            }
            disabled={loading}
          >
            {loading
              ? "Updating..."
              : "Complete Day →"}
          </button>

        </div>

      </section>

    </section>
  );
}


/* =====================================================
   QUIZ
===================================================== */

function QuizScreen({
  learning,
  onSubmit,
  onDashboard,
  loading,
}) {
  const questions =
    learning?.assessment
      ?.questions || [];

  const [answers, setAnswers] =
    useState([]);


  useEffect(() => {
    function preventQuizCopy(event) {
      event.preventDefault();
    }

    function preventQuizKeyboard(event) {
      const key =
        event.key.toLowerCase();

      if (
        (event.ctrlKey ||
          event.metaKey) &&
        [
          "c",
          "v",
          "x",
          "a",
        ].includes(key)
      ) {
        event.preventDefault();
      }
    }

    document.addEventListener(
      "copy",
      preventQuizCopy
    );

    document.addEventListener(
      "cut",
      preventQuizCopy
    );

    document.addEventListener(
      "paste",
      preventQuizCopy
    );

    document.addEventListener(
      "contextmenu",
      preventQuizCopy
    );

    document.addEventListener(
      "keydown",
      preventQuizKeyboard
    );

    return () => {
      document.removeEventListener(
        "copy",
        preventQuizCopy
      );

      document.removeEventListener(
        "cut",
        preventQuizCopy
      );

      document.removeEventListener(
        "paste",
        preventQuizCopy
      );

      document.removeEventListener(
        "contextmenu",
        preventQuizCopy
      );

      document.removeEventListener(
        "keydown",
        preventQuizKeyboard
      );
    };
  }, []);


  useEffect(() => {
    setAnswers(
      Array(
        questions.length
      ).fill("")
    );
  }, [
    learning?.assessment,
    questions.length,
  ]);


  function selectAnswer(
    index,
    answer
  ) {
    setAnswers(
      (previous) => {
        const next = [
          ...previous,
        ];

        next[index] = answer;

        return next;
      }
    );
  }


  function submit(event) {
    event.preventDefault();

    if (
      answers.length !==
      questions.length
    ) {
      return;
    }

    if (
      answers.some(
        (answer) =>
          !answer
      )
    ) {
      return;
    }

    onSubmit(answers);
  }


  if (questions.length === 0) {
    return (
      <section className="page-section">

        <div className="empty-card">

          <h2>
            Assessment unavailable
          </h2>

          <p>
            No quiz questions were
            returned by the backend.
          </p>

          <button
            type="button"
            className="primary-button"
            onClick={
              onDashboard
            }
          >
            Dashboard
          </button>

        </div>

      </section>
    );
  }


  return (
    <section className="quiz-page">

      <div className="quiz-header">

        <div>

          <span className="eyebrow">
            ASSESSMENT
          </span>

          <h1>
            {learning?.assessment
              ?.topic ||
              learning?.current_topic
                ?.topic ||
              "Topic Assessment"}
          </h1>

          <p>
            Answer all questions.
            You need 100% to advance.
          </p>

        </div>


        <button
          type="button"
          className="secondary-button"
          onClick={
            onDashboard
          }
        >
          Dashboard
        </button>

      </div>


      <form
        className="quiz-form"
        onSubmit={submit}
      >

        {questions.map(
          (
            question,
            questionIndex
          ) => (
            <div
              className="question-card"
              key={
                questionIndex
              }
            >

              <div className="question-number">
                Question{" "}
                {questionIndex + 1}
                {" / "}
                {questions.length}
              </div>

              <h2>
                {question.question}
              </h2>

              <div className="option-list">

                {(question.options ||
                  []
                ).map(
                  (
                    option,
                    optionIndex
                  ) => {

                    const selected =
                      answers[
                        questionIndex
                      ] === option;

                    return (
                      <label
                        className={
                          selected
                            ? "quiz-option selected"
                            : "quiz-option"
                        }
                        key={
                          optionIndex
                        }
                      >

                        <input
                          type="radio"
                          name={`question-${questionIndex}`}
                          value={
                            option
                          }
                          checked={
                            selected
                          }
                          onChange={() =>
                            selectAnswer(
                              questionIndex,
                              option
                            )
                          }
                        />

                        <span>
                          {option}
                        </span>

                      </label>
                    );
                  }
                )}

              </div>

            </div>
          )
        )}


        <button
          type="submit"
          className="primary-button quiz-submit"
          disabled={
            loading ||
            answers.some(
              (answer) =>
                !answer
            )
          }
        >
          {loading
            ? "Evaluating..."
            : "Submit Assessment →"}
        </button>

      </form>

    </section>
  );
}


/* =====================================================
   RESULT
===================================================== */

function ResultScreen({
  learning,
  onDashboard,
  onActivity,
}) {
  const evaluation =
    learning?.evaluation || {};

  const questionResults =
    Array.isArray(
      evaluation.question_results
    )
      ? evaluation.question_results
      : [];


  let score = Number(
    evaluation.score
  );

  if (
    !Number.isFinite(score) ||
    score < 0
  ) {
    score = 0;
  }


  let total = Number(
    evaluation.total
  );

  if (
    !Number.isFinite(total) ||
    total <= 0
  ) {
    total = Number(
      evaluation.total_questions
    );
  }


  if (
    !Number.isFinite(total) ||
    total <= 0
  ) {
    total =
      questionResults.length;
  }


  const percentage =
    Number(
      evaluation.percentage
    ) ||
    (
      total > 0
        ? Math.round(
            (score / total) *
              100
          )
        : 0
    );


  const passed =
    percentage === 100;


  const action =
    learning?.adaptive_action
      ?.action;


  return (
    <section className="result-page">

      <div className="result-card">

        <span className="eyebrow">
          ASSESSMENT RESULT
        </span>


        <h1>
          {passed
            ? "Assessment completed"
            : "Keep learning and try again"}
        </h1>


        <div className="score-display">

          <strong>
            {score}
          </strong>

          <span>
            /{total}
          </span>

        </div>


        <div className="percentage-display">
          {percentage}%
        </div>


        <p>
          {passed
            ? "You achieved 100%. The next week is unlocked."
            : "You need 100% to advance. A focused review will help strengthen the weak areas."}
        </p>


        {evaluation.weak_topics
          ?.length > 0 && (
          <div className="weak-topics">

            <strong>
              Topics to review
            </strong>

            <div className="tag-list">

              {evaluation.weak_topics.map(
                (
                  topic,
                  index
                ) => (
                  <span
                    className="tag"
                    key={
                      index
                    }
                  >
                    {topic}
                  </span>
                )
              )}

            </div>

          </div>
        )}


        <div className="result-actions">

          <button
            type="button"
            className="secondary-button"
            onClick={
              onDashboard
            }
          >
            Dashboard
          </button>


          <button
            type="button"
            className="primary-button"
            onClick={
              onActivity
            }
          >
            {passed
              ? "Continue to Next Week →"
              : "Start Review →"}
          </button>

        </div>


        {action && (
          <div className="adaptive-message">

            Adaptive action:{" "}

            {action}

          </div>
        )}

      </div>

    </section>
  );
}


/* =====================================================
   DASHBOARD
===================================================== */

function ProgressScreen({
  progress,
  onContinue,
  onProfile,
}) {
  if (!progress) {
    return (
      <section className="page-section">

        <div className="empty-card">

          <h2>
            No progress available
          </h2>

          <button
            type="button"
            className="primary-button"
            onClick={
              onProfile
            }
          >
            Open Profile
          </button>

        </div>

      </section>
    );
  }


  const completed =
    Number(
      progress.completed_activities
    ) || 0;


  const notDone =
    Number(
      progress.not_done_activities
    ) || 0;


  const total =
    Number(
      progress.total_activities
    ) || 0;


  const remaining =
    Math.max(
      total - completed,
      0
    );


  const completedPercentage =
    Number(
      progress.completed_percentage
    ) ||
    Number(
      progress.completion_percentage
    ) ||
    0;


  const remainingPercentage =
    Math.max(
      100 -
        completedPercentage,
      0
    );


  const currentTopic =
    progress.current_topic?.topic ||
    progress.current_topic?.title ||
    progress.current_week_details?.topic ||
    null;

  const currentTopicDesc =
    progress.current_topic?.description ||
    progress.current_week_details?.description ||
    null;

  const goal =
    progress.goal ||
    progress.state?.goal ||
    null;


  return (
    <section className="dashboard-page">

      <div className="page-heading">

        <span className="eyebrow">
          DASHBOARD
        </span>

        <h1>
          {goal
            ? `Learning: ${goal}`
            : "Your learning progress"}
        </h1>

        <p>
          Track completed, not done,
          and remaining activities.
        </p>

      </div>


      <div className="progress-overview">

        <div className="progress-main">

          <span>
            Overall completion
          </span>

          <strong>
            {completedPercentage}%
          </strong>

          <div className="progress-bar">

            <div
              className="progress-bar-fill"
              style={{
                width:
                  `${completedPercentage}%`,
              }}
            />

          </div>

        </div>

      </div>


      {currentTopic && (
        <div className="current-topic-banner">
          <span className="eyebrow">
            WEEK {progress.current_week} — CURRENT TOPIC
          </span>
          <h2>{currentTopic}</h2>
          {currentTopicDesc && (
            <p>{currentTopicDesc}</p>
          )}
        </div>
      )}


      <div className="progress-grid">

        <ProgressCard
          label="Completed"
          count={
            completed
          }
          percentage={
            completedPercentage
          }
        />

        <ProgressCard
          label="Not Done"
          count={
            notDone
          }
          percentage={
            total > 0
              ? Math.round(
                  (notDone /
                    total) *
                    100
                )
              : 0
          }
        />

        <ProgressCard
          label="Remaining"
          count={
            remaining
          }
          percentage={
            remainingPercentage
          }
        />

        <ProgressCard
          label="Total"
          count={
            total
          }
          percentage={100}
        />

      </div>


      <div className="dashboard-details">

        <div>

          <span className="section-label">
            CURRENT WEEK
          </span>

          <strong>
            Week{" "}
            {progress.current_week}
          </strong>

        </div>


        <div>

          <span className="section-label">
            CURRENT DAY
          </span>

          <strong>
            Day{" "}
            {progress.current_day}
          </strong>

        </div>


        <div>

          <span className="section-label">
            TOPIC
          </span>

          <strong>
            {currentTopic || "Learning"}
          </strong>

        </div>

      </div>


      <div className="dashboard-actions">

        <button
          type="button"
          className="secondary-button"
          onClick={
            onProfile
          }
        >
          Profile
        </button>


        <button
          type="button"
          className="primary-button"
          onClick={
            onContinue
          }
        >
          Continue Learning →
        </button>

      </div>

    </section>
  );
}


/* =====================================================
   FIELD
===================================================== */

function Field({
  label,
  required,
  type = "text",
  value,
  onChange,
  placeholder,
}) {
  return (
    <label className="field">

      <span className="field-label">

        {label}

        {required && (
          <span className="required-mark">
            *
          </span>
        )}

      </span>


      <input
        className="text-input"
        type={type}
        value={value}
        required={required}
        onChange={(event) =>
          onChange(
            event.target.value
          )
        }
        placeholder={
          placeholder
        }
      />

    </label>
  );
}


/* =====================================================
   NUMBER FIELD
===================================================== */

function NumberField({
  label,
  required,
  min,
  value,
  onChange,
}) {
  return (
    <label className="field">

      <span className="field-label">

        {label}

        {required && (
          <span className="required-mark">
            *
          </span>
        )}

      </span>


      <input
        className="text-input"
        type="number"
        min={min}
        value={value}
        required={required}
        onChange={(event) =>
          onChange(
            event.target.value
          )
        }
      />

    </label>
  );
}


/* =====================================================
   SELECT FIELD
===================================================== */

function SelectField({
  label,
  required,
  value,
  onChange,
  options,
}) {
  return (
    <label className="field">

      <span className="field-label">

        {label}

        {required && (
          <span className="required-mark">
            *
          </span>
        )}

      </span>


      <select
        className="text-input"
        value={value}
        required={required}
        onChange={(event) =>
          onChange(
            event.target.value
          )
        }
      >

        {options.map(
          ([
            optionValue,
            labelText,
          ]) => (
            <option
              value={
                optionValue
              }
              key={
                optionValue
              }
            >
              {labelText}
            </option>
          )
        )}

      </select>

    </label>
  );
}


/* =====================================================
   CONTENT SECTION
===================================================== */

function ContentSection({
  title,
  text,
  items,
  ordered = false,
}) {
  return (
    <section className="content-section">

      <div className="section-label">
        {title}
      </div>


      {text && (
        <p className="content-text">
          {text}
        </p>
      )}


      {items?.length > 0 &&
        (
          ordered ? (
            <ol className="content-list">

              {items.map(
                (
                  item,
                  index
                ) => (
                  <li
                    key={
                      index
                    }
                  >
                    {item}
                  </li>
                )
              )}

            </ol>
          ) : (
            <ul className="content-list">

              {items.map(
                (
                  item,
                  index
                ) => (
                  <li
                    key={
                      index
                    }
                  >
                    {item}
                  </li>
                )
              )}

            </ul>
          )
        )}

    </section>
  );
}


/* =====================================================
   SUMMARY ITEM
===================================================== */

function SummaryItem({
  label,
  value,
}) {
  return (
    <div className="summary-item">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


/* =====================================================
   PROGRESS CARD
===================================================== */

function ProgressCard({
  label,
  count,
  percentage,
}) {
  return (
    <div className="progress-card">

      <span>
        {label}
      </span>

      <strong>
        {count}
      </strong>

      <small>
        {percentage}%
      </small>

    </div>
  );
}


export default App;