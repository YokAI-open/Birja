import { PortfolioDeleteForm } from "@/components/PortfolioDeleteForm";

/** Authenticated owner/tab recovery; never a selected financial target. */
export default function PortfolioDeletionPage() {
  return (
    <div className="app-page flex max-w-2xl flex-col gap-6 text-base leading-6 wrap-anywhere">
      <h1 className="app-heading">Deletion request</h1>
      <PortfolioDeleteForm metadataBusy={false} recoveryOnly refreshMetadata={() => undefined} />
    </div>
  );
}
