export type Email = {
  id: number;
  gmail_message_id: string;
  thread_id: number | null;
  sender: string;
  recipients: string;
  subject: string;
  body: string;
  received_at: string | null;
  category: string | null;
  priority: number | null;
  summary: string | null;
  expected_action: string | null;
  status: string | null;
};

export type Summary = {
  date: string;
  total_emails: number;
  high_priority_count: number;
  category_counts: Record<string, number>;
  overview: string;
  top_priority_emails: {
    id: number;
    sender: string;
    subject: string;
    priority: number;
    category: string;
    summary: string | null;
    expected_action: string | null;
    reason: string;
  }[];
};
