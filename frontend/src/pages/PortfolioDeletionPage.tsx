import { PortfolioDeleteForm } from "@/components/PortfolioDeleteForm";

/** Authenticated owner/tab recovery; never a selected financial target. */
export default function PortfolioDeletionPage() {
  return (
    <div className="my-8 flex min-w-0 max-w-[1440px] flex-col gap-4 text-base leading-6 wrap-anywhere">
      <h1 className="text-[32px] leading-10 font-medium">Deletion request</h1>
      <PortfolioDeleteForm metadataBusy={false} recoveryOnly refreshMetadata={() => undefined} />
    </div>
  );
}
