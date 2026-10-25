import reviewLedger from '../data/reviewLedger.json';

type LedgerRecord = {
  id: string;
  catalogueApproval: { status: string | null; label: string };
  evidenceReview: { humanReviewStatus: string | null; label: string; evidenceFile: string };
  userApproval: { status: string };
  contentFlags?: { flag: string; claimId: string; status: string; evidenceLevel: string; file: string }[];
};

const LEDGER = new Map<string, LedgerRecord>(
  (reviewLedger.records as LedgerRecord[]).map((record) => [record.id, record]),
);

/** C-06: show the catalogue approval and the pending evidence review side by side, never just one of them.
 *  Claim-level reviewFlags (e.g. the ming_02 carrier-nature flag) follow as extra badges, verbatim from the ledger. */
export function ReviewStatusBadges({ steleId, compact = false }: { steleId: string; compact?: boolean }) {
  const record = LEDGER.get(steleId);
  if (!record) return null;
  const base = compact ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5';
  return (
    <div className="flex flex-wrap items-center gap-1.5" data-testid="review-status-badges" data-stele-id={steleId}>
      <span
        className={`${base} rounded border border-emerald-700/60 text-emerald-300 bg-emerald-950/30`}
        title={`目录 sourceVerification.status = ${record.catalogueApproval.status}；批准人、日期、范围：${record.userApproval.status}`}
      >
        {record.catalogueApproval.label}
      </span>
      <span
        className={`${base} rounded border border-amber-700/60 text-amber-300 bg-amber-950/30`}
        title={`${record.evidenceReview.evidenceFile} · human_review_status = ${record.evidenceReview.humanReviewStatus}`}
      >
        {record.evidenceReview.label}
      </span>
      {(record.contentFlags ?? []).map((flag) => (
        <span
          key={`${flag.claimId}:${flag.flag}`}
          data-testid="content-flag"
          className={`${base} rounded border border-rose-700/60 text-rose-300 bg-rose-950/30`}
          title={`${flag.file} · ${flag.claimId} · status = ${flag.status} · ${flag.evidenceLevel}`}
        >
          {flag.flag}
        </span>
      ))}
    </div>
  );
}
