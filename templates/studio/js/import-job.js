/**
 * Travelogue Studio · import job/response helpers (shared by api + import-flow).
 */

export function importResponseData(result) {
  return (result && (result.data || result.body)) || {};
}

/** Succeeded jobs should always expose result; synthesize when only tripId is present. */
export function normalizeCompletedImportJob(job) {
  if (!job || typeof job !== "object") return job;
  if (job.status !== "succeeded") return job;
  if (job.result && typeof job.result === "object") return job;
  var tripId = job.tripId;
  if (!tripId) return job;
  return Object.assign({}, job, {
    result: {
      tripId: tripId,
      previewUrl: "/" + tripId + "/index.html",
      title: "",
      photoCount: 0,
      featuredCount: 0,
      segmentCount: 0,
      clusterNotice: "",
    },
  });
}
