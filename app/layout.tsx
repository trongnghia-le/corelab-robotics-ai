import type { Metadata } from "next";
import { Provider } from "@/components/provider";
import { Shell } from "@/components/shell";
import "./globals.css";
import "katex/dist/katex.min.css";
export const metadata: Metadata = {
  title: "CoreLab · Personal Research Workspace",
  description:
    "Local-first learning for Robotics, Computer Vision, Reinforcement Learning and Cognitive Robotics.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <body>
        <Provider>
          <Shell>{children}</Shell>
        </Provider>
      </body>
    </html>
  );
}
