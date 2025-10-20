"use client"

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Wrench } from 'lucide-react';

interface ToolCallCardProps {
  toolCall: {
    tool_call_id: string;
    tool_name: string;
    arguments?: Record<string, unknown>;
    result?: Record<string, unknown>;
  };
}

export function ToolCallCard({ toolCall }: ToolCallCardProps) {
  return (
    <Card className="mb-3">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Wrench className="h-4 w-4" />
          Tool Call: {toolCall.tool_name}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {toolCall.arguments && (
          <div>
            <Badge variant="outline" className="mb-1">Arguments</Badge>
            <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">
              {JSON.stringify(toolCall.arguments, null, 2)}
            </pre>
          </div>
        )}
        {toolCall.result && (
          <div>
            <Badge variant="outline" className="mb-1">Result</Badge>
            <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">
              {JSON.stringify(toolCall.result, null, 2)}
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
