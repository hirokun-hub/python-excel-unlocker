export type DriveFolder = {
  id: string;
  name: string;
  modifiedTime?: string;
  parents?: string[];
  iconLink?: string;
};

export type FoldersResponse = {
  nextPageToken?: string;
  files: DriveFolder[];
};

export type BreadcrumbItem = { id: string; name: string };
