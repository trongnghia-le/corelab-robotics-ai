"use client";
import Link from "next/link";
import {
  knowledgeTypes,
  knowledgeTypeFor,
  knowledgeTypeInfo,
} from "@/lib/assessment";
import { weaknessUrl } from "@/lib/weaknesses";
import { practices } from "@/lib/practice";
import type { TopicPayload } from "@/lib/types";
import { useI18n } from "@/lib/i18n";
export function AssessmentMethods({
  id,
  data,
}: {
  id: string;
  data: TopicPayload;
}) {
  const { tx } = useI18n();
  return (
    <section className="panel assessment-methods">
      <h2>
        {tx(
          "Choose evidence that fits the knowledge",
          "Chọn cách kiểm chứng phù hợp với loại kiến thức",
        )}
      </h2>
      <p className="small muted">
        {tx(
          "Knowledge type chooses how to assess. C/M/I/T describes what the evidence demonstrates.",
          "Loại kiến thức quyết định cách kiểm tra. C/M/I/T mô tả bằng chứng chứng tỏ điều gì.",
        )}
      </p>
      <div className="method-grid">
        {knowledgeTypes.map((type) => {
          const info = knowledgeTypeInfo[type];
          const q = data.assessment?.questions.find(
            (q) => knowledgeTypeFor(q) === type,
          );
          const skill = data.practiceSkills?.find((s) =>
            s.knowledgeTypes.includes(type),
          );
          const lab = type === "implementation" && ["M02", "PY01"].includes(id);
          const assignment =
            type === "implementation" &&
            practices.some((p) => p.topicId === id);
          return (
            <div key={type}>
              <strong>
                {info.label} — {info.goal}
              </strong>
              <p>{q?.recommendedMethod ?? info.method}</p>
              {type === "implementation" && (lab || assignment) ? (
                <>
                  <Link className="text-link" href={`/practice?topic=${id}`}>
                    {lab
                      ? tx(
                          "Open signed local verifier",
                          "Mở bộ kiểm chứng cục bộ có chữ ký",
                        )
                      : tx("Open local assignment", "Mở bài tập cục bộ")}
                  </Link>
                  <small>
                    {lab
                      ? tx(
                          "Supported A0 reports can demonstrate I.",
                          "Báo cáo A0 được hỗ trợ có thể chứng minh I.",
                        )
                      : tx(
                          "No signed verifier for this assignment; results remain self-reported.",
                          "Bài này chưa có bộ kiểm chứng có chữ ký; kết quả vẫn là tự báo cáo.",
                        )}
                  </small>
                </>
              ) : q ? (
                <>
                  <a className="text-link" href={`#assessment-${q.id}`}>
                    {q.kind === "short"
                      ? tx("Open rubric response", "Mở câu trả lời rubric")
                      : tx("Open check questions", "Mở câu hỏi kiểm tra")}
                  </a>
                  <small>
                    {q.kind === "short"
                      ? tx(
                          "Open responses remain unverified.",
                          "Câu trả lời mở vẫn chưa được kiểm chứng.",
                        )
                      : tx(
                          "Objective answers use the authored contract.",
                          "Đáp án khách quan dùng hợp đồng đã biên soạn.",
                        )}
                  </small>
                </>
              ) : skill ? (
                <>
                  <Link
                    className="text-link"
                    href={weaknessUrl(id, skill.tag) + "#targeted-practice"}
                  >
                    {tx(
                      `Open focused ${type} practice`,
                      `Mở bài luyện tập tập trung (${type})`,
                    )}
                  </Link>
                  <small>
                    {tx(
                      "Focused practice does not replace the full diagnostic.",
                      "Luyện tập tập trung không thay cho bài kiểm tra đầy đủ.",
                    )}
                  </small>
                </>
              ) : (
                <span className="muted small">
                  {tx(
                    "No authored assessment available for this type yet.",
                    "Loại này chưa có bài kiểm tra được biên soạn.",
                  )}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
