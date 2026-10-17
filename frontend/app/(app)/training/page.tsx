import { Badge, Card, PageHeader } from "@/components/ui";
export default function Training() {
  return (<><PageHeader title="Training" /><Card><Badge tone="warn">Coming later</Badge>
    <h2 className="mt-3 font-semibold">Model training is not available yet</h2>
    <p className="mt-1 text-sm text-muted">No training jobs are running. Planned: versioned dataset snapshots, train/validation/test splits, GPU-worker jobs with logs and checkpoints, held-out evaluation, and promotion only after explicit approval.</p></Card></>);
}
