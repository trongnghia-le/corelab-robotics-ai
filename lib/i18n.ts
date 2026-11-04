import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { LANG_COOKIE, LANG_STORAGE, parseLang, type Lang } from "./lang";

export type { Lang } from "./lang";

/** English is the source of truth; Vietnamese must define every key. */
const en = {
  // common
  "common.details": "Details",
  "common.saving": "Saving…",
  "common.noPrereqs": "No prerequisites.",
  // shell
  "shell.skip": "Skip navigation",
  "shell.mainNav": "Main navigation",
  "shell.closeMenu": "Close menu",
  "shell.openMenu": "Open menu",
  "shell.workspace": "Personal workspace",
  "shell.workspaceSub": "Robotics & AI learning",
  "shell.captionLearn": "YOUR LEARNING FLOW",
  "shell.captionMore": "MORE",
  "shell.localTitle": "Local-first. Yours.",
  "shell.localBody": "Your data stays on your machine. No cloud, no API.",
  "shell.crumb": "Workspace",
  "shell.local": "Local workspace",
  "shell.language": "Language",
  "shell.footer1": "Understand principles. Implement independently. Verify.",
  "shell.footer2": "Check → Learn → Derive → Implement → Verify → Transfer",
  "nav.dashboard": "Dashboard",
  "nav.roadmap": "Roadmap",
  "nav.lessons": "Lessons",
  "nav.practice": "Practice",
  "nav.review": "Review",
  "nav.paths": "Learning paths",
  "nav.tutor": "AI Tutor handoff",
  "nav.sources": "References",
  "nav.settings": "Data & settings",
  "nav.lab": "Extra practice lab",
  // statuses
  "status.notStarted": "Not started",
  "status.practised": "Practised",
  "status.mastered": "Mastered",
  "status.selfRated": "Self-rated",
  "status.reviewDue": "Review due",
  "dim.C": "Conceptual Understanding",
  "dim.M": "Mathematical Reasoning",
  "dim.I": "Independent Implementation",
  "dim.T": "Transfer & Retention",
  "matrix.evidence": "Evidence L{n}",
  "matrix.none": "No evidence yet",
  // sessions / lesson
  "session.learn": "Learn",
  "session.practice": "Practice",
  "session.build": "Build",
  "session.review": "Review",
  "lesson.sessions": "Study sessions",
  "lesson.sessionCount": "{n} sessions",
  "lesson.sessionsDone": "{n}/{total} sessions",
  "lesson.progress": "Lesson progress",
  "lesson.sessionOf": "Session {n} of {total} · {name}",
  "lesson.markDone": "Mark session done",
  "lesson.labDone": "Lab done",
  "lesson.done": "done",
  "lesson.next": "Next: {name}",
  "lesson.testYourself": "Check what you know now",
  "lesson.savedDone": "Session saved as done. Mastery is unchanged.",
  "lesson.savedUndone": "Session marked as not done.",
  "lesson.readingNote":
    "Marking a session only saves your progress; it does not increase mastery.",
  "lesson.showAnswers": "Show answers",
  "lesson.hideAnswers": "Hide answers",
  "lesson.answersHidden":
    "Exercise answers are hidden. Try the exercises first, then reveal them to check your work.",
  "lesson.contents": "Contents",
  "lesson.inThis": "IN THIS LESSON",
  "lesson.after": "AFTER THIS LESSON",
  "lesson.video": "Recommended video",
  "lesson.interactive": "Interactive exploration",
  "lesson.flow": "Check → Learn → Derive → Implement → Verify → Transfer",
  "lesson.notTranslated":
    "Not translated yet. Showing the English lesson for this topic.",
  // topic page
  "topic.unableTitle": "Unable to open topic",
  "topic.backRoadmap": "Back to Roadmap",
  "topic.checkTitle": "Check · {title}",
  "topic.checkKnow": "Check what you know",
  "topic.copyContext": "Copy Learning Context",
  "topic.contextCopied": "Learning Context copied.",
  "topic.copyFailed": "Unable to copy.",
  "topic.pinned": "Pinned {id} as the current focus.",
  "topic.pinFocus": "Pin focus",
  "topic.focusPinned": "Focus pinned",
  "topic.readLesson": "Read lesson",
  "topic.viewContext": "View generated Learning Context",
  "topic.prereqs": "Suggested prerequisites",
  "topic.prereqWarn":
    "Some prerequisites are not mastered yet. You can still study this topic; consider checking the foundations first.",
  "topic.prevLesson": "Previous lesson in the library",
  "topic.nextLesson": "Next lesson in the library",
  "topic.buildsOn": "Topics that build on this foundation",
  // notebook
  "notebook.title": "Research notebook",
  "notebook.intro":
    "Record reasoning, experimental results, and open questions. Self-assessments remain separate from verified competence.",
  "notebook.type": "Entry type",
  "notebook.note": "Note",
  "notebook.difficulty": "Knowledge debt · difficulty",
  "notebook.practice": "Practice results",
  "notebook.self": "Self-assessment · provisional",
  "notebook.time": "Time (minutes)",
  "notebook.level": "Self-assessed level",
  "notebook.placeholder":
    "What did I try? Which results can I not explain yet?",
  "notebook.save": "Save entry",
  "notebook.saved": "Notebook entry saved locally.",
  // assessment
  "assist.label": "How much help did you use?",
  "assist.A0": "No help (A0)",
  "assist.A1": "Used a hint (A1)",
  "assist.A2": "Looked at an example (A2)",
  "assist.A3": "Saw the solution (A3)",
  "assist.note":
    "Only answers given with no help (A0) count towards mastery. Answers with a hint, an example or the solution are saved as practice.",
  "question.critical": "MUST GET RIGHT",
  "question.auto": "AUTO-CHECKED",
  "question.rubric": "SELF-CHECK · NOT AUTO-GRADED",
  "question.skill": "Skill",
  "question.number": "Answer (use a decimal point)",
  "question.numberPlaceholder": "Enter a number…",
  "question.response": "Rubric response",
  "assess.masteredTitle": "What counts as mastered",
  "assess.gateC":
    "Score at least 80% with no help (A0), and no must-get-right question wrong.",
  "assess.gateM": "Numerical answers are within the allowed tolerance.",
  "assess.gateI": "Implement it yourself and import a valid local test report.",
  "assess.gateT": "Repeat the check without help after at least 7 days.",
  "assess.levelsNote":
    "Level 2 needs conceptual, numerical and implementation evidence. Levels 3 and 4 need unfamiliar transfer tasks or independently reviewed research; this quiz does not certify those.",
  "assess.cmit":
    "C = concept, M = mathematics, I = implementation, T = transfer and retention. These are the four kinds of evidence the engine records.",
  "assess.assistNote":
    "A0 = no help, A1 = hint, A2 = example, A3 = saw the solution.",
  "assess.practiceInstructions": "Open practice instructions",
  "assess.methods": "How each kind of knowledge is checked",
  "assess.checkTitle": "Check what you know",
  "assess.tryFirst":
    "Try before viewing solutions. Short responses are saved with a rubric and are not automatically graded.",
  "assess.submit": "Submit and save answers",
  "assess.none": "No check available for this topic yet",
  "assess.noneNote":
    "Record notes and self-study results in the notebook. They remain unverified.",
  "assess.result": "Result · {score}%",
  "assess.passed": "Passed with no help (A0)",
  "assess.passedHelp": "Passed with help · practice only",
  "assess.tryAgain": "Study and try again",
  "assess.saved": "Saved in SQLite",
  "assess.rubric": "Review against rubric",
  "assess.rubricShort": "Rubric",
  "assess.rubricOnly": "Rubric only",
  "assess.correct": "Correct",
  "assess.notYet": "Not yet correct",
  "assess.revisit": "Revisit the theory",
  "assess.practiceWeak": "Practice Weaknesses",
  "assess.history": "History",
  "assess.focused": "Focused practice",
  "assess.check": "Check",
  "assess.noAttempts":
    "No attempts yet. Missing evidence does not mean missing ability.",
  "assess.labReport": "Fixed-test report",
  "assess.labIndependent":
    "Independent implementation evidence with self-declared assistance.",
  "assess.labAssisted": "Assisted · practice only.",
  "assess.historyNote":
    "History is kept after an unsuccessful review. A failed attempt creates a review gap.",
  "assess.saveFail": "Unable to save attempt.",
  // catalog
  "cat.road.eyebrow": "THE LONG-TERM MAP",
  "cat.road.title": "Knowledge roadmap",
  "cat.road.desc":
    "{n} topics connected by prerequisites. A long-term map, not a mandatory checklist.",
  "cat.lessons.eyebrow": "LEARN FROM FIRST PRINCIPLES",
  "cat.lessons.title": "Go beyond reading. Understand deeply.",
  "cat.lessons.desc":
    "{n} authored lessons. Start with foundations and progress step by step.",
  "cat.review.eyebrow": "REVIEW AND CHECK",
  "cat.review.title": "Check what you know.",
  "cat.review.desc":
    "Short checks, clear feedback, and a record of your progress.",
  "cat.review.banner":
    "A no-help (A0) check counts towards mastery only with a score of at least 80% and no must-get-right question wrong. Open responses use a rubric and never automatically increase mastery.",
  "cat.search": "Search by topic name or ID…",
  "cat.viewMode": "View mode",
  "cat.list": "List",
  "cat.graph": "Graph",
  "cat.fDomain": "Filter by domain",
  "cat.allDomains": "All domains",
  "cat.fPriority": "Filter by priority",
  "cat.allPriorities": "All priorities",
  "cat.p0": "Core",
  "cat.p1": "Applied",
  "cat.p2": "Extension",
  "cat.fStatus": "Filter by status",
  "cat.allStatuses": "All statuses",
  "cat.topic1": "{n} topic",
  "cat.topicN": "{n} topics",
  "cat.none": "No topics found",
  "cat.noneNote": "Try a shorter search or remove a filter.",
  "cat.clear": "Clear filters",
  "cat.complete": "Complete lesson + check",
  "cat.overviewOnly": "Overview · full lesson not yet available",
  "cat.prereqs": "{n} prerequisites",
  "cat.foundation": "Foundation",
  "cat.open": "Open {id}",
  "cat.cardLesson": "Theory · Examples · Practice",
  "cat.cardCheck": "Concept · Math · Rubric",
  "cat.note":
    "P0 Core foundations · P1 Application · P2 Research extensions. Every topic is accessible; prerequisites guide learning without locking pages.",
  // graph
  "graph.chain": "Selected prerequisite chain",
  "graph.scope": "Scope: {domain}",
  "graph.nodes": "{n} nodes · drag to pan, scroll to zoom.",
  "graph.focus": "Focus prerequisite chain",
  "graph.currentDomain": "Current domain",
  "graph.prereqs": "Prerequisites",
  "graph.open": "Open topic details",
  "graph.legend": "Colour legend",
  "graph.outside": "Dashed border: prerequisite from another domain",
  "graph.note":
    "Select a node to inspect it. Prerequisites outside the domain remain visible to preserve relationships. The list provides equivalent keyboard navigation.",
  // dashboard
  "dash.eyebrow": "YOUR ROBOTICS & AI LEARNING LAB",
  "dash.title": "Your Robotics & AI journey.",
  "dash.desc":
    "Understand the foundations. Build the algorithms. Discover what you can do independently.",
  "dash.myPath": "My learning path",
  "dash.next": "YOUR NEXT STEP",
  "dash.kind.learn": "LEARN",
  "dash.kind.assess": "CHECK",
  "dash.kind.practice": "PRACTICE",
  "dash.kind.review": "REVIEW",
  "dash.kind.explore": "EXPLORE",
  "dash.tryNext": "Try this next",
  "dash.cta.weak": "Practice weak skill",
  "dash.cta.review": "Review now",
  "dash.cta.assess": "Check what you know",
  "dash.cta.learn": "Continue learning",
  "dash.pace": "Progress by competence, at your own pace",
  "dash.noRec.title": "Your next foundation",
  "dash.noRec.body":
    "No lesson currently matches what you have mastered. Open the Roadmap to choose a foundation to work on.",
  "dash.openRoadmap": "Open Roadmap",
  "dash.labEyebrow": "FROM FIRST PRINCIPLES TO ROBOT BEHAVIOR",
  "dash.labTitle": "Make the connection.",
  "dash.openLab": "Open Extra practice lab",
  "dash.exploreCurriculum": "Explore Robotics & AI curriculum",
  "dash.labNote":
    "Objective practice and C/M checks have their own evidence record.",
  "dash.progressLabel": "Your progress",
  "dash.mastered": "Topics mastered",
  "dash.ofTopics": "of {n} curriculum topics",
  "dash.attempted": "Topics practised",
  "dash.throughChecks": "through topic checks",
  "dash.due": "Reviews due",
  "dash.dueNote": "return when it is time to retrieve",
  "dash.evidenceNote":
    "Mastery reflects the checks you passed; reading and practice do not automatically increase it.",
  "dash.startNote": "Not started is a starting point, not a score of zero.",
  "dash.exploreEyebrow": "EXPLORE YOUR INTERESTS",
  "dash.exploreTitle": "Where will you go next?",
  "dash.fullCurriculum": "Full curriculum",
  "dash.exploreNote":
    "Start with a foundation or follow your curiosity. The roadmap includes future topics; authored lessons are counted separately.",
  "dash.domainDefault": "Explore this part of the curriculum.",
  "dash.curriculumTopics": "{n} curriculum topics",
  "dash.lesson1": "{n} authored lesson",
  "dash.lessonN": "{n} authored lessons",
  "dash.masteredN1": "{n} topic mastered",
  "dash.masteredN": "{n} topics mastered",
  "dash.weak": "Weaknesses to Review",
  "dash.weakCounts": "{m} mistakes · {a} failed attempts",
  "dash.noWeak":
    "No active weaknesses. Past mistakes remain available in Practice.",
  "dash.noWeakYet":
    "Not enough data yet. Mistakes in auto-checked questions will appear here; open responses never count as errors.",
  "dash.recent": "Recent activity",
  "dash.ready1": "Your workspace is ready.",
  "dash.ready2": "Start with one small question.",
  "dash.firstLesson": "Open your first lesson",
  "dash.return": "Return to",
  "dash.readOn": "Last session",
  "dash.continue": "Continue",
  "dash.strengths": "Mastered topics",
  "dash.q1": "Implement & test independently",
  "dash.q1b": "Practice outside the browser, at your own pace.",
  "dash.q2": "Take your questions to AI Tutor",
  "dash.q2b": "Copy the context; keep your progress in CoreLab.",
  "dash.branches": "Suitable parallel learning branches ({n})",
  "dash.act.focused": "Focused practice",
  "dash.act.check": "Check",
  "dash.act.read": "Lesson read",
  "dash.act.practice": "Practice",
  "dash.act.note": "Note",
  "dash.act.difficulty": "Difficulty recorded",
  "dash.act.self": "Self-assessed",
  "dash.act.ai": "AI feedback · unverified",
  "dash.act.sessionDone": "{name} session done",
  "dash.act.sessionUndone": "{name} session reopened",
  "dom.Mathematics": "The language of motion and uncertainty.",
  "dom.Programming": "Turn ideas into reliable algorithms.",
  "dom.Machine Learning": "Patterns, losses and generalization.",
  "dom.Computer Vision": "Connect pixels to geometry.",
  "dom.Robotics": "Frames, motion, estimation and control.",
  "dom.Reinforcement & Robot Learning":
    "Make decisions from rewards and dynamics.",
  "dom.Embodied & Cognitive Robotics": "Connect perception, memory and action.",
  "dom.Scientific Research": "Design experiments. Question results.",
  "dom.Hardware & Embedded":
    "Sensors, motors, power and the firmware that runs them.",
  "dom.Capstone": "One robot that uses everything you learned.",
  "shell.desk": "Desk",
  "shell.deskHint":
    "Open the study desk beside this window: notes, exercises and code",
  // practice & tools
  "practice.eyebrow": "IMPLEMENT → VERIFY → TRANSFER",
  "practice.title": "Implement independently. Verify your work.",
  "practice.desc":
    "Write code in VS Code and run tests in your own terminal. CoreLab does not execute code submitted through the browser.",
  "practice.sections": "Practice sections",
  "practice.assignments": "Assignments",
  "practice.weaknesses": "My Weaknesses",
  "weak.eyebrow": "PRACTICE → MY WEAKNESSES",
  "weak.title": "Practice the skill behind the mistake.",
  "weak.desc":
    "Objective errors become a focused queue. Correcting a skill preserves its history and does not certify a whole topic.",
  "weak.active": "Active weakness",
  "weak.assisted": "Practiced with assistance",
  "weak.corrected": "Independently corrected",
  "weak.retention": "Due for retention review",
  "paths.eyebrow": "FROM ZERO TO INDEPENDENT RESEARCH",
  "paths.title": "One path, many open branches.",
  "paths.desc":
    "Follow prerequisites and progress. You do not need to finish an entire domain to start a suitable branch.",
  "tutor.eyebrow": "CHATGPT PROJECT · MANUAL HANDOFF",
  "tutor.title": "One tutor. One source of truth.",
  "tutor.desc":
    "Bring the right context into your conversation. CoreLab keeps your progress on your machine.",
  "settings.eyebrow": "YOUR DATA, ON YOUR MACHINE",
  "settings.desc":
    "Back up progress, preserve your history, and control your personal data.",
  "sources.eyebrow": "STUDY THE ORIGINALS",
  "sources.desc":
    "Study original courses, texts, and official documentation. External links require Internet; lessons and progress work locally.",
} as const;

export type Dict = Record<keyof typeof en, string>;

const vi: Dict = {
  "common.details": "Chi tiết",
  "common.saving": "Đang lưu…",
  "common.noPrereqs": "Không có kiến thức tiên quyết.",
  "shell.skip": "Bỏ qua điều hướng",
  "shell.mainNav": "Điều hướng chính",
  "shell.closeMenu": "Đóng menu",
  "shell.openMenu": "Mở menu",
  "shell.workspace": "Không gian cá nhân",
  "shell.workspaceSub": "Học Robotics & AI",
  "shell.captionLearn": "LỘ TRÌNH HỌC CỦA BẠN",
  "shell.captionMore": "THÊM",
  "shell.localTitle": "Chạy cục bộ. Của bạn.",
  "shell.localBody": "Dữ liệu nằm trên máy của bạn. Không cloud, không API.",
  "shell.crumb": "Không gian học",
  "shell.local": "Không gian cục bộ",
  "shell.language": "Ngôn ngữ",
  "shell.footer1": "Hiểu nguyên lý. Tự cài đặt. Kiểm chứng.",
  "shell.footer2":
    "Kiểm tra → Học → Suy luận → Cài đặt → Kiểm chứng → Vận dụng",
  "nav.dashboard": "Tổng quan",
  "nav.roadmap": "Lộ trình",
  "nav.lessons": "Bài học",
  "nav.practice": "Luyện tập",
  "nav.review": "Ôn tập",
  "nav.paths": "Đường học",
  "nav.tutor": "Chuyển cho AI Tutor",
  "nav.sources": "Tài liệu tham khảo",
  "nav.settings": "Dữ liệu & cài đặt",
  "nav.lab": "Phòng luyện tập thêm",
  "status.notStarted": "Chưa bắt đầu",
  "status.practised": "Đã luyện tập",
  "status.mastered": "Đã nắm vững",
  "status.selfRated": "Tự đánh giá",
  "status.reviewDue": "Đến hạn ôn tập",
  "dim.C": "Hiểu khái niệm",
  "dim.M": "Suy luận toán học",
  "dim.I": "Tự cài đặt",
  "dim.T": "Vận dụng & ghi nhớ",
  "matrix.evidence": "Bằng chứng L{n}",
  "matrix.none": "Chưa có bằng chứng",
  "session.learn": "Học",
  "session.practice": "Luyện tập",
  "session.build": "Thực hành",
  "session.review": "Ôn lại",
  "lesson.sessions": "Các buổi học",
  "lesson.sessionCount": "{n} buổi",
  "lesson.sessionsDone": "{n}/{total} buổi",
  "lesson.progress": "Tiến độ bài học",
  "lesson.sessionOf": "Buổi {n}/{total} · {name}",
  "lesson.markDone": "Đánh dấu hoàn thành buổi học",
  "lesson.labDone": "Đã làm xong lab",
  "lesson.done": "đã xong",
  "lesson.next": "Tiếp theo: {name}",
  "lesson.testYourself": "Kiểm tra kiến thức ngay",
  "lesson.savedDone": "Đã lưu buổi học là hoàn thành. Mức nắm vững không đổi.",
  "lesson.savedUndone": "Đã bỏ đánh dấu hoàn thành buổi học.",
  "lesson.readingNote":
    "Đánh dấu buổi học chỉ lưu tiến độ, không làm tăng mức nắm vững.",
  "lesson.showAnswers": "Hiện đáp án",
  "lesson.hideAnswers": "Ẩn đáp án",
  "lesson.answersHidden":
    "Đáp án đang được ẩn. Hãy tự làm bài tập trước, rồi mở đáp án để đối chiếu.",
  "lesson.contents": "Mục lục",
  "lesson.inThis": "TRONG BÀI NÀY",
  "lesson.after": "SAU BÀI HỌC NÀY",
  "lesson.video": "Video đề xuất",
  "lesson.interactive": "Khám phá tương tác",
  "lesson.flow": "Kiểm tra → Học → Suy luận → Cài đặt → Kiểm chứng → Vận dụng",
  "lesson.notTranslated":
    "Chưa có bản dịch. Đang hiển thị bài học tiếng Anh cho chủ đề này.",
  "topic.unableTitle": "Không mở được chủ đề",
  "topic.backRoadmap": "Quay lại Lộ trình",
  "topic.checkTitle": "Kiểm tra · {title}",
  "topic.checkKnow": "Kiểm tra kiến thức",
  "topic.copyContext": "Sao chép Learning Context",
  "topic.contextCopied": "Đã sao chép Learning Context.",
  "topic.copyFailed": "Không sao chép được.",
  "topic.pinned": "Đã ghim {id} làm trọng tâm hiện tại.",
  "topic.pinFocus": "Ghim trọng tâm",
  "topic.focusPinned": "Đã ghim trọng tâm",
  "topic.readLesson": "Đọc bài học",
  "topic.viewContext": "Xem Learning Context đã tạo",
  "topic.prereqs": "Kiến thức tiên quyết gợi ý",
  "topic.prereqWarn":
    "Một số kiến thức tiên quyết chưa được nắm vững. Bạn vẫn có thể học chủ đề này; hãy cân nhắc kiểm tra phần nền tảng trước.",
  "topic.prevLesson": "Bài trước trong thư viện",
  "topic.nextLesson": "Bài tiếp theo trong thư viện",
  "topic.buildsOn": "Các chủ đề xây dựng trên nền tảng này",
  "notebook.title": "Sổ ghi chép nghiên cứu",
  "notebook.intro":
    "Ghi lại lập luận, kết quả thí nghiệm và các câu hỏi còn mở. Tự đánh giá luôn tách biệt với năng lực đã được kiểm chứng.",
  "notebook.type": "Loại ghi chú",
  "notebook.note": "Ghi chú",
  "notebook.difficulty": "Chỗ còn vướng · khó khăn",
  "notebook.practice": "Kết quả luyện tập",
  "notebook.self": "Tự đánh giá · tạm thời",
  "notebook.time": "Thời gian (phút)",
  "notebook.level": "Mức tự đánh giá",
  "notebook.placeholder":
    "Mình đã thử gì? Kết quả nào mình chưa giải thích được?",
  "notebook.save": "Lưu ghi chú",
  "notebook.saved": "Đã lưu ghi chú trên máy.",
  "assist.label": "Bạn đã dùng bao nhiêu trợ giúp?",
  "assist.A0": "Không trợ giúp (A0)",
  "assist.A1": "Đã dùng gợi ý (A1)",
  "assist.A2": "Đã xem ví dụ (A2)",
  "assist.A3": "Đã xem lời giải (A3)",
  "assist.note":
    "Chỉ các câu trả lời không trợ giúp (A0) mới được tính vào mức nắm vững. Câu trả lời có gợi ý, ví dụ hoặc lời giải được lưu như bài luyện tập.",
  "question.critical": "PHẢI ĐÚNG",
  "question.auto": "TỰ ĐỘNG CHẤM",
  "question.rubric": "TỰ ĐỐI CHIẾU · KHÔNG TỰ CHẤM",
  "question.skill": "Kỹ năng",
  "question.number": "Đáp án (dùng dấu chấm thập phân)",
  "question.numberPlaceholder": "Nhập một số…",
  "question.response": "Câu trả lời theo rubric",
  "assess.masteredTitle": "Thế nào là đã nắm vững",
  "assess.gateC":
    "Đạt ít nhất 80% khi không trợ giúp (A0), và không sai câu nào thuộc loại phải đúng.",
  "assess.gateM": "Đáp án bằng số nằm trong sai số cho phép.",
  "assess.gateI": "Tự cài đặt và nhập một báo cáo kiểm thử cục bộ hợp lệ.",
  "assess.gateT": "Làm lại bài kiểm tra không trợ giúp sau ít nhất 7 ngày.",
  "assess.levelsNote":
    "Mức 2 cần bằng chứng về khái niệm, tính toán và cài đặt. Mức 3 và 4 cần bài vận dụng mới hoặc nghiên cứu được người khác đánh giá độc lập; bài kiểm tra này không xác nhận các mức đó.",
  "assess.cmit":
    "C = khái niệm, M = toán học, I = cài đặt, T = vận dụng và ghi nhớ. Đây là bốn loại bằng chứng mà hệ thống ghi nhận.",
  "assess.assistNote":
    "A0 = không trợ giúp, A1 = gợi ý, A2 = ví dụ, A3 = đã xem lời giải.",
  "assess.practiceInstructions": "Mở hướng dẫn luyện tập",
  "assess.methods": "Cách kiểm tra từng loại kiến thức",
  "assess.checkTitle": "Kiểm tra kiến thức",
  "assess.tryFirst":
    "Hãy tự làm trước khi xem lời giải. Câu trả lời ngắn được lưu cùng rubric và không được tự động chấm.",
  "assess.submit": "Nộp và lưu câu trả lời",
  "assess.none": "Chủ đề này chưa có bài kiểm tra",
  "assess.noneNote":
    "Hãy ghi chú và kết quả tự học vào sổ ghi chép. Chúng chưa được kiểm chứng.",
  "assess.result": "Kết quả · {score}%",
  "assess.passed": "Đạt khi không trợ giúp (A0)",
  "assess.passedHelp": "Đạt khi có trợ giúp · chỉ tính là luyện tập",
  "assess.tryAgain": "Hãy học lại rồi thử lần nữa",
  "assess.saved": "Đã lưu trong SQLite",
  "assess.rubric": "Đối chiếu với rubric",
  "assess.rubricShort": "Rubric",
  "assess.rubricOnly": "Chỉ rubric",
  "assess.correct": "Đúng",
  "assess.notYet": "Chưa đúng",
  "assess.revisit": "Xem lại lý thuyết",
  "assess.practiceWeak": "Luyện tập điểm yếu",
  "assess.history": "Lịch sử",
  "assess.focused": "Luyện tập tập trung",
  "assess.check": "Kiểm tra",
  "assess.noAttempts":
    "Chưa có lần làm nào. Chưa có dữ liệu không có nghĩa là chưa có năng lực.",
  "assess.labReport": "Báo cáo kiểm thử cố định",
  "assess.labIndependent":
    "Bằng chứng tự cài đặt, mức trợ giúp do bạn tự khai báo.",
  "assess.labAssisted": "Có trợ giúp · chỉ tính là luyện tập.",
  "assess.historyNote":
    "Lịch sử được giữ lại sau một lần ôn tập chưa đạt. Một lần làm sai sẽ tạo ra một khoảng trống cần ôn.",
  "assess.saveFail": "Không lưu được lần làm bài.",
  "cat.road.eyebrow": "BẢN ĐỒ DÀI HẠN",
  "cat.road.title": "Lộ trình kiến thức",
  "cat.road.desc":
    "{n} chủ đề được nối với nhau bằng kiến thức tiên quyết. Đây là bản đồ dài hạn, không phải danh sách bắt buộc.",
  "cat.lessons.eyebrow": "HỌC TỪ NGUYÊN LÝ CƠ BẢN",
  "cat.lessons.title": "Không chỉ đọc. Hãy hiểu sâu.",
  "cat.lessons.desc":
    "{n} bài học đã biên soạn. Bắt đầu từ nền tảng và tiến lên từng bước.",
  "cat.review.eyebrow": "ÔN TẬP VÀ KIỂM TRA",
  "cat.review.title": "Kiểm tra kiến thức của bạn.",
  "cat.review.desc":
    "Bài kiểm tra ngắn, phản hồi rõ ràng và lưu lại tiến độ của bạn.",
  "cat.review.banner":
    "Một bài kiểm tra không trợ giúp (A0) chỉ được tính vào mức nắm vững khi đạt ít nhất 80% và không sai câu nào thuộc loại phải đúng. Câu trả lời mở dùng rubric và không bao giờ tự động tăng mức nắm vững.",
  "cat.search": "Tìm theo tên hoặc mã chủ đề…",
  "cat.viewMode": "Chế độ xem",
  "cat.list": "Danh sách",
  "cat.graph": "Đồ thị",
  "cat.fDomain": "Lọc theo lĩnh vực",
  "cat.allDomains": "Tất cả lĩnh vực",
  "cat.fPriority": "Lọc theo mức ưu tiên",
  "cat.allPriorities": "Mọi mức ưu tiên",
  "cat.p0": "Cốt lõi",
  "cat.p1": "Ứng dụng",
  "cat.p2": "Mở rộng",
  "cat.fStatus": "Lọc theo trạng thái",
  "cat.allStatuses": "Mọi trạng thái",
  "cat.topic1": "{n} chủ đề",
  "cat.topicN": "{n} chủ đề",
  "cat.none": "Không tìm thấy chủ đề",
  "cat.noneNote": "Thử từ khóa ngắn hơn hoặc bỏ bớt bộ lọc.",
  "cat.clear": "Xóa bộ lọc",
  "cat.complete": "Bài học đầy đủ + bài kiểm tra",
  "cat.overviewOnly": "Tổng quan · chưa có bài học đầy đủ",
  "cat.prereqs": "{n} kiến thức tiên quyết",
  "cat.foundation": "Nền tảng",
  "cat.open": "Mở {id}",
  "cat.cardLesson": "Lý thuyết · Ví dụ · Luyện tập",
  "cat.cardCheck": "Khái niệm · Toán · Rubric",
  "cat.note":
    "P0 Nền tảng cốt lõi · P1 Ứng dụng · P2 Mở rộng nghiên cứu. Chủ đề nào cũng mở được; kiến thức tiên quyết chỉ định hướng, không khóa trang.",
  "graph.chain": "Chuỗi tiên quyết đã chọn",
  "graph.scope": "Phạm vi: {domain}",
  "graph.nodes": "{n} nút · kéo để di chuyển, cuộn để phóng to.",
  "graph.focus": "Chọn chuỗi tiên quyết",
  "graph.currentDomain": "Lĩnh vực hiện tại",
  "graph.prereqs": "Kiến thức tiên quyết",
  "graph.open": "Mở chi tiết chủ đề",
  "graph.legend": "Chú thích màu",
  "graph.outside": "Viền đứt nét: kiến thức tiên quyết thuộc lĩnh vực khác",
  "graph.note":
    "Chọn một nút để xem chi tiết. Các kiến thức tiên quyết ngoài lĩnh vực vẫn hiển thị để giữ nguyên quan hệ. Danh sách cung cấp cách điều hướng tương đương bằng bàn phím.",
  "dash.eyebrow": "PHÒNG HỌC ROBOTICS & AI CỦA BẠN",
  "dash.title": "Hành trình Robotics & AI của bạn.",
  "dash.desc":
    "Hiểu nền tảng. Tự xây dựng thuật toán. Khám phá những gì bạn có thể làm độc lập.",
  "dash.myPath": "Đường học của tôi",
  "dash.next": "BƯỚC TIẾP THEO CỦA BẠN",
  "dash.kind.learn": "HỌC",
  "dash.kind.assess": "KIỂM TRA",
  "dash.kind.practice": "LUYỆN TẬP",
  "dash.kind.review": "ÔN TẬP",
  "dash.kind.explore": "KHÁM PHÁ",
  "dash.tryNext": "Thử việc này tiếp theo",
  "dash.cta.weak": "Luyện kỹ năng còn yếu",
  "dash.cta.review": "Ôn tập ngay",
  "dash.cta.assess": "Kiểm tra kiến thức",
  "dash.cta.learn": "Tiếp tục học",
  "dash.pace": "Tiến bộ theo năng lực, theo nhịp của riêng bạn",
  "dash.noRec.title": "Nền tảng tiếp theo của bạn",
  "dash.noRec.body":
    "Hiện chưa có bài học nào phù hợp với những gì bạn đã nắm vững. Hãy mở Lộ trình để chọn một nền tảng.",
  "dash.openRoadmap": "Mở Lộ trình",
  "dash.labEyebrow": "TỪ NGUYÊN LÝ CƠ BẢN ĐẾN HÀNH VI ROBOT",
  "dash.labTitle": "Kết nối các mảnh ghép.",
  "dash.openLab": "Mở phòng luyện tập thêm",
  "dash.exploreCurriculum": "Khám phá chương trình Robotics & AI",
  "dash.labNote":
    "Luyện tập theo mục tiêu và kiểm tra C/M có hồ sơ bằng chứng riêng.",
  "dash.progressLabel": "Tiến độ của bạn",
  "dash.mastered": "Chủ đề đã nắm vững",
  "dash.ofTopics": "trên {n} chủ đề của chương trình",
  "dash.attempted": "Chủ đề đã luyện tập",
  "dash.throughChecks": "qua các bài kiểm tra chủ đề",
  "dash.due": "Lượt ôn tập đến hạn",
  "dash.dueNote": "quay lại khi đến lúc nhớ lại",
  "dash.evidenceNote":
    "Mức nắm vững phản ánh các bài kiểm tra bạn đã đạt; đọc và luyện tập không tự động làm tăng nó.",
  "dash.startNote":
    "Chưa bắt đầu chỉ là điểm xuất phát, không phải điểm không.",
  "dash.exploreEyebrow": "KHÁM PHÁ SỞ THÍCH CỦA BẠN",
  "dash.exploreTitle": "Bạn sẽ đi đâu tiếp theo?",
  "dash.fullCurriculum": "Toàn bộ chương trình",
  "dash.exploreNote":
    "Bắt đầu từ nền tảng hoặc theo sự tò mò của bạn. Lộ trình gồm cả các chủ đề tương lai; số bài học đã biên soạn được đếm riêng.",
  "dash.domainDefault": "Khám phá phần này của chương trình.",
  "dash.curriculumTopics": "{n} chủ đề trong chương trình",
  "dash.lesson1": "{n} bài học đã biên soạn",
  "dash.lessonN": "{n} bài học đã biên soạn",
  "dash.masteredN1": "{n} chủ đề đã nắm vững",
  "dash.masteredN": "{n} chủ đề đã nắm vững",
  "dash.weak": "Điểm yếu cần ôn",
  "dash.weakCounts": "{m} lỗi · {a} lần làm chưa đạt",
  "dash.noWeak":
    "Không có điểm yếu đang mở. Các lỗi trước đây vẫn xem được trong Luyện tập.",
  "dash.noWeakYet":
    "Chưa đủ dữ liệu. Các lỗi ở câu hỏi tự động chấm sẽ xuất hiện ở đây; câu trả lời mở không bao giờ bị tính là lỗi.",
  "dash.recent": "Hoạt động gần đây",
  "dash.ready1": "Không gian học của bạn đã sẵn sàng.",
  "dash.ready2": "Hãy bắt đầu với một câu hỏi nhỏ.",
  "dash.firstLesson": "Mở bài học đầu tiên",
  "dash.return": "Quay lại",
  "dash.readOn": "Buổi gần nhất",
  "dash.continue": "Tiếp tục",
  "dash.strengths": "Chủ đề đã nắm vững",
  "dash.q1": "Tự cài đặt & kiểm thử",
  "dash.q1b": "Luyện tập ngoài trình duyệt, theo nhịp của bạn.",
  "dash.q2": "Mang câu hỏi của bạn đến AI Tutor",
  "dash.q2b": "Sao chép ngữ cảnh; tiến độ vẫn nằm trong CoreLab.",
  "dash.branches": "Các nhánh học song song phù hợp ({n})",
  "dash.act.focused": "Luyện tập tập trung",
  "dash.act.check": "Kiểm tra",
  "dash.act.read": "Đã đọc bài",
  "dash.act.practice": "Luyện tập",
  "dash.act.note": "Ghi chú",
  "dash.act.difficulty": "Đã ghi lại khó khăn",
  "dash.act.self": "Tự đánh giá",
  "dash.act.ai": "Phản hồi AI · chưa kiểm chứng",
  "dash.act.sessionDone": "Xong buổi {name}",
  "dash.act.sessionUndone": "Mở lại buổi {name}",
  "dom.Mathematics": "Ngôn ngữ của chuyển động và sự bất định.",
  "dom.Programming": "Biến ý tưởng thành thuật toán đáng tin cậy.",
  "dom.Machine Learning": "Mẫu, hàm mất mát (loss) và khả năng khái quát hóa.",
  "dom.Computer Vision": "Nối điểm ảnh với hình học.",
  "dom.Robotics": "Hệ tọa độ, chuyển động, ước lượng và điều khiển.",
  "dom.Reinforcement & Robot Learning":
    "Ra quyết định từ phần thưởng và động lực học.",
  "dom.Embodied & Cognitive Robotics": "Nối nhận thức, trí nhớ và hành động.",
  "dom.Scientific Research": "Thiết kế thí nghiệm. Đặt câu hỏi cho kết quả.",
  "dom.Hardware & Embedded":
    "Cảm biến, động cơ, nguồn điện và firmware điều khiển chúng.",
  "dom.Capstone": "Một robot vận dụng mọi điều bạn đã học.",
  "shell.desk": "Bàn học",
  "shell.deskHint": "Mở bàn học bên cạnh cửa sổ này: ghi chú, bài tập và code",
  "practice.eyebrow": "CÀI ĐẶT → KIỂM CHỨNG → VẬN DỤNG",
  "practice.title": "Tự cài đặt. Tự kiểm chứng.",
  "practice.desc":
    "Viết code trong VS Code và chạy test trong terminal của bạn. CoreLab không chạy code được gửi qua trình duyệt.",
  "practice.sections": "Các phần luyện tập",
  "practice.assignments": "Bài tập",
  "practice.weaknesses": "Điểm yếu của tôi",
  "weak.eyebrow": "LUYỆN TẬP → ĐIỂM YẾU CỦA TÔI",
  "weak.title": "Luyện kỹ năng đứng sau lỗi sai.",
  "weak.desc":
    "Các lỗi sai khách quan trở thành hàng đợi luyện tập tập trung. Sửa được một kỹ năng sẽ giữ lại lịch sử và không xác nhận cả chủ đề.",
  "weak.active": "Điểm yếu đang mở",
  "weak.assisted": "Đã luyện với trợ giúp",
  "weak.corrected": "Đã tự sửa được",
  "weak.retention": "Đến hạn ôn lại để ghi nhớ",
  "paths.eyebrow": "TỪ SỐ KHÔNG ĐẾN NGHIÊN CỨU ĐỘC LẬP",
  "paths.title": "Một đường học, nhiều nhánh mở.",
  "paths.desc":
    "Đi theo kiến thức tiên quyết và tiến độ của bạn. Bạn không cần học hết một lĩnh vực để bắt đầu một nhánh phù hợp.",
  "tutor.eyebrow": "CHATGPT PROJECT · CHUYỂN THỦ CÔNG",
  "tutor.title": "Một gia sư. Một nguồn dữ liệu duy nhất.",
  "tutor.desc":
    "Mang đúng ngữ cảnh vào cuộc trò chuyện. CoreLab giữ tiến độ của bạn trên máy.",
  "settings.eyebrow": "DỮ LIỆU CỦA BẠN, TRÊN MÁY CỦA BẠN",
  "settings.desc":
    "Sao lưu tiến độ, giữ lại lịch sử và kiểm soát dữ liệu cá nhân của bạn.",
  "sources.eyebrow": "HỌC TỪ NGUỒN GỐC",
  "sources.desc":
    "Học từ các khóa học, giáo trình và tài liệu chính thức gốc. Liên kết ngoài cần Internet; bài học và tiến độ hoạt động cục bộ.",
};

export const dictionaries: Record<Lang, Dict> = { en, vi };

export function translate(
  lang: Lang,
  key: keyof Dict,
  vars?: Record<string, string | number>,
) {
  const text = dictionaries[lang][key] ?? en[key];
  return vars
    ? text.replace(/\{(\w+)\}/g, (_, name) => String(vars[name] ?? `{${name}}`))
    : text;
}

/** "5 h 30 min" / "5 giờ 30 phút". */
export function formatDuration(minutes: number, lang: Lang = "en") {
  const h = Math.floor(minutes / 60),
    m = Math.round(minutes % 60);
  const hour = lang === "vi" ? "giờ" : "h",
    min = lang === "vi" ? "phút" : "min";
  if (!h) return `${m} ${min}`;
  return m ? `${h} ${hour} ${m} ${min}` : `${h} ${hour}`;
}

const recommendationText: [RegExp, (m: RegExpMatchArray) => string][] = [
  [
    /^Practice (.+): (\d+) recorded mistakes\. Focus on this skill rather than repeating the lesson\.$/,
    (m) =>
      `Luyện kỹ năng ${m[1]}: đã ghi nhận ${m[2]} lỗi. Hãy tập trung vào kỹ năng này thay vì học lại cả bài.`,
  ],
  [
    /^Review due: check retention without viewing the solution\.$/,
    () => "Đến hạn ôn tập: kiểm tra trí nhớ mà không xem lời giải.",
  ],
  [
    /^The latest attempt revealed a gap; read the feedback and try again independently\.$/,
    () =>
      "Lần làm gần nhất cho thấy còn lỗ hổng; hãy đọc phản hồi rồi tự thử lại.",
  ],
  [
    /^You have shown you understand the concepts; next, implement independently and test your work\.$/,
    () =>
      "Bạn đã chứng tỏ hiểu khái niệm; tiếp theo hãy tự cài đặt và kiểm thử bài làm.",
  ],
  [
    /^A foundation needed for your pinned goal (.+); its prerequisites are now mastered\.$/,
    (m) =>
      `Nền tảng cần cho mục tiêu bạn đã ghim ${m[1]}; các kiến thức tiên quyết của nó đã được nắm vững.`,
  ],
  [
    /^Its prerequisites are mastered\. This is the next step in building your foundations\.$/,
    () =>
      "Các kiến thức tiên quyết đã được nắm vững. Đây là bước tiếp theo để xây nền tảng.",
  ],
  [
    /^Not started yet\. Begin with a foundation that has no prerequisites\.$/,
    () =>
      "Chưa bắt đầu. Hãy bắt đầu với một nền tảng không có kiến thức tiên quyết.",
  ],
  [
    /^Review the linked reasoning and solve a fresh focused set with no help \(A0\)\. Focused correction is separate from mastering the whole topic\.$/,
    () =>
      "Xem lại phần lập luận được liên kết và làm một bộ câu hỏi tập trung mới, không trợ giúp (A0). Sửa một kỹ năng không đồng nghĩa với nắm vững cả chủ đề.",
  ],
  [
    /^Implement the assignment independently, run local tests, and import the report\.$/,
    () => "Tự làm bài tập, chạy test cục bộ rồi nhập báo cáo.",
  ],
  [
    /^Take the short check first with no help \(A0\); study and address gaps after your attempt\.$/,
    () =>
      "Làm bài kiểm tra ngắn trước, không trợ giúp (A0); sau đó học và bù các chỗ còn thiếu.",
  ],
];

/** Translate the engine's English recommendation sentences for display. */
export function localizeRecommendation(text: string, lang: Lang) {
  if (lang === "en") return text;
  for (const [pattern, build] of recommendationText) {
    const match = text.match(pattern);
    if (match) return build(match);
  }
  return text;
}

const planText: [string, string][] = [
  [
    "An authored, focused set. Correct A0 answers can repair this skill; this set never satisfies full diagnostic mastery gates.",
    "Một bộ câu hỏi tập trung đã biên soạn. Trả lời đúng khi không trợ giúp (A0) có thể sửa kỹ năng này; bộ này không thay cho bài kiểm tra đầy đủ để nắm vững chủ đề.",
  ],
  [
    "No fresh variants remain. A due question can be reused once after seven days; beyond that, review feedback or take the full diagnostic. New variants must be authored.",
    "Không còn biến thể mới. Một câu đến hạn có thể được dùng lại một lần sau bảy ngày; ngoài ra hãy xem lại phản hồi hoặc làm bài kiểm tra đầy đủ. Biến thể mới cần được biên soạn.",
  ],
  [
    "No authored variants exist for this skill yet. Review the linked concept or retry the diagnostic; no replacement questions are invented.",
    "Kỹ năng này chưa có biến thể được biên soạn. Hãy xem lại khái niệm liên quan hoặc làm lại bài kiểm tra; hệ thống không tự bịa câu hỏi thay thế.",
  ],
  [
    "Repeated mistakes suggest checking this unverified foundation; this is a recommendation, not proof of a prerequisite deficit.",
    "Các lỗi lặp lại gợi ý nên kiểm tra nền tảng chưa được kiểm chứng này; đây chỉ là gợi ý, không chứng minh bạn thiếu kiến thức tiên quyết.",
  ],
];

/** Translate the fixed focused-practice sentences produced by the server. */
export function localizePlanText(text: string, lang: Lang) {
  if (lang === "en") return text;
  return planText.find(([en]) => en === text)?.[1] ?? text;
}

type I18n = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: keyof Dict, vars?: Record<string, string | number>) => string;
  /** Inline pair for long-tail copy: English first, Vietnamese second. */
  tx: (english: string, vietnamese: string) => string;
};

const fallback: I18n = {
  lang: "en",
  setLang: () => {},
  t: (key, vars) => translate("en", key, vars),
  tx: (english) => english,
};
const I18nContext = createContext<I18n>(fallback);

export function I18nProvider({
  initial,
  children,
}: {
  initial: Lang;
  children: ReactNode;
}) {
  const [lang, setLangState] = useState<Lang>(initial);
  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    try {
      localStorage.setItem(LANG_STORAGE, next);
    } catch {}
    document.cookie = `${LANG_COOKIE}=${next}; path=/; max-age=31536000; SameSite=Lax`;
    document.documentElement.lang = next;
  }, []);
  useEffect(() => {
    // localStorage is the source of truth; repair a missing or stale cookie.
    let stored: Lang | null = null;
    try {
      const raw = localStorage.getItem(LANG_STORAGE);
      if (raw) stored = parseLang(raw);
    } catch {}
    if (stored && stored !== initial) setLang(stored);
    else document.documentElement.lang = initial;
  }, [initial, setLang]);
  const t = useCallback<I18n["t"]>(
    (key, vars) => translate(lang, key, vars),
    [lang],
  );
  const tx = useCallback<I18n["tx"]>(
    (english, vietnamese) => (lang === "vi" ? vietnamese : english),
    [lang],
  );
  return createElement(
    I18nContext.Provider,
    { value: { lang, setLang, t, tx } },
    children,
  );
}

export function useI18n() {
  return useContext(I18nContext);
}
