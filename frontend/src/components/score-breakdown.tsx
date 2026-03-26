"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { CatfishResult } from "@/types/analysis";
import { MetadataPanel } from "./metadata-panel";
import { ReverseImagePanel } from "./reverse-image-panel";
import { FaceAnalysisPanel } from "./face-analysis-panel";

interface ScoreBreakdownProps {
  result: CatfishResult;
}

function riskBadge(score: number) {
  if (score < 30)
    return <Badge className="bg-green-500/15 text-green-400 border-green-500/30 text-xs">{score}</Badge>;
  if (score < 65)
    return <Badge className="bg-yellow-500/15 text-yellow-400 border-yellow-500/30 text-xs">{score}</Badge>;
  return <Badge className="bg-red-500/15 text-red-400 border-red-500/30 text-xs">{score}</Badge>;
}

export function ScoreBreakdown({ result }: ScoreBreakdownProps) {
  const sections = [
    {
      id: "reverse",
      title: "Reverse Image Search",
      weight: "50%",
      score: result.reverse_image.risk_score,
      content: <ReverseImagePanel data={result.reverse_image} />,
    },
    {
      id: "face",
      title: "Face Analysis",
      weight: "30%",
      score: result.face_analysis.risk_score,
      content: <FaceAnalysisPanel data={result.face_analysis} />,
    },
    {
      id: "metadata",
      title: "Image Metadata",
      weight: "20%",
      score: result.metadata.risk_score,
      content: <MetadataPanel data={result.metadata} />,
    },
  ];

  return (
    <Accordion type="multiple" className="w-full" defaultValue={["reverse"]}>
      {sections.map((section) => (
        <AccordionItem key={section.id} value={section.id}>
          <AccordionTrigger className="hover:no-underline">
            <div className="flex items-center gap-3 text-sm">
              {riskBadge(section.score)}
              <span>{section.title}</span>
              <span className="text-xs text-muted-foreground">
                ({section.weight} weight)
              </span>
            </div>
          </AccordionTrigger>
          <AccordionContent>{section.content}</AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}
