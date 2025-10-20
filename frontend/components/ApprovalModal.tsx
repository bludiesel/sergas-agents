"use client"

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface Recommendation {
  recommendation_id: string;
  category: string;
  title: string;
  description: string;
  confidence_score: number;
  priority: string;
  next_steps: string[];
}

interface ApprovalModalProps {
  request: {
    run_id: string;
    recommendations: Recommendation[];
  };
  onApprove: (modifiedData?: Record<string, unknown>) => Promise<void>;
  onReject: (reason: string) => Promise<void>;
}

export function ApprovalModal({ request, onApprove, onReject }: ApprovalModalProps) {
  const [open, setOpen] = useState(true);
  const [rejectionReason, setRejectionReason] = useState('');
  const [loading, setLoading] = useState(false);

  const handleApprove = async () => {
    setLoading(true);
    try {
      await onApprove();
      setOpen(false);
    } catch (error) {
      console.error('Approval failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    setLoading(true);
    try {
      await onReject(rejectionReason || 'User rejected');
      setOpen(false);
    } catch (error) {
      console.error('Rejection failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityVariant = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'critical':
        return 'destructive';
      case 'high':
        return 'default';
      default:
        return 'secondary';
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Approval Required</DialogTitle>
          <DialogDescription>
            Review the following recommendations and approve or reject.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {request.recommendations.map((rec) => (
            <div
              key={rec.recommendation_id}
              className="border border-gray-200 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold">{rec.title}</h3>
                <div className="flex gap-2">
                  <Badge variant={getPriorityVariant(rec.priority)}>
                    {rec.priority}
                  </Badge>
                  <Badge variant="outline">{rec.confidence_score}% confident</Badge>
                </div>
              </div>

              <p className="text-gray-600 mb-3">{rec.description}</p>

              <div className="bg-gray-50 rounded p-3">
                <p className="text-sm font-medium mb-2">Next Steps:</p>
                <ul className="list-disc list-inside space-y-1">
                  {rec.next_steps.map((step, idx) => (
                    <li key={idx} className="text-sm text-gray-700">{step}</li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>

        <DialogFooter>
          <div className="flex gap-2 w-full">
            <input
              type="text"
              placeholder="Rejection reason (optional)"
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded"
              disabled={loading}
            />
            <Button
              variant="outline"
              onClick={handleReject}
              disabled={loading}
            >
              {loading ? 'Rejecting...' : 'Reject'}
            </Button>
            <Button
              onClick={handleApprove}
              disabled={loading}
            >
              {loading ? 'Approving...' : 'Approve'}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
