import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { google, drive_v3 } from "googleapis";
import { authOptions } from "@/auth";
import pLimit from "p-limit";

const FOLDER_MIME_TYPE = "application/vnd.google-apps.folder";
const esc = (s: string) => s.replace(/['\\]/g, "\\$&");

// --- Path Generation Logic ---
const driveNameCache = new Map<string, string>();
const fileNameCache = new Map<string, { name: string; parents?: string[] }>();
const limit = pLimit(8); // Limit concurrency to 8 to avoid rate limiting

async function getFileMetadata(drive: drive_v3.Drive, fileId: string): Promise<{ name: string; parents?: string[] }> {
  if (fileNameCache.has(fileId)) {
    return fileNameCache.get(fileId)!;
  }
  try {
    const { data } = await drive.files.get({
      fileId,
      fields: "id,name,parents",
      supportsAllDrives: true,
    });
    fileNameCache.set(fileId, data);
    return data;
  } catch (error) {
    // console.error(`Failed to fetch metadata for fileId: ${fileId}`, error);
    const inaccessibleResult = { name: "(アクセス権なし)", parents: [] };
    fileNameCache.set(fileId, inaccessibleResult);
    return inaccessibleResult;
  }
}

async function getDisplayPath(drive: drive_v3.Drive, file: drive_v3.Schema$File): Promise<string> {
  if (!file.id || !file.name) return "(不明なパス)";

  const names: string[] = [file.name];
  let currentParentId = file.parents?.[0];
  let rootLabel = "マイドライブ";

  if (file.driveId) {
    if (!driveNameCache.has(file.driveId)) {
      try {
        const { data } = await drive.drives.get({ driveId: file.driveId, fields: "name" });
        driveNameCache.set(file.driveId, data.name || "共有ドライブ");
      } catch (error) {
        // console.error(`Failed to fetch drive name for driveId: ${file.driveId}`, error);
        driveNameCache.set(file.driveId, "共有ドライブ");
      }
    }
    rootLabel = driveNameCache.get(file.driveId)!;
  }

  let depth = 0;
  const maxDepth = 20; // Prevent infinite loops
  let truncated = false;

  while (currentParentId && depth < maxDepth) {
    const parentFile = await getFileMetadata(drive, currentParentId);
    if (parentFile.name === "(アクセス権なし)") {
      truncated = true;
      break;
    }
    names.unshift(parentFile.name);
    currentParentId = parentFile.parents?.[0];
    depth++;
  }

  const path = truncated ? `... / ${names.join(" / ")}` : names.join(" / ");
  return `${rootLabel} / ${path}`;
}


// --- API Route Handler ---
export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const parentId = searchParams.get("parentId") || "root";
  const q = (searchParams.get("q") || "").trim();
  const pageToken = searchParams.get("pageToken") || undefined;

  try {
    const session = await getServerSession(authOptions);
    const accessToken = session?.accessToken;
    if (!accessToken) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const auth = new google.auth.OAuth2();
    auth.setCredentials({ access_token: accessToken });
    const drive = google.drive({ version: "v3", auth });

    const qParts = [`mimeType='${FOLDER_MIME_TYPE}'`, "trashed=false"];
    const listParams: drive_v3.Params$Resource$Files$List = {
      orderBy: "modifiedTime desc, name asc",
      pageSize: 100,
      fields: "files(id,name,mimeType,parents,modifiedTime,driveId),nextPageToken",
      supportsAllDrives: true,
      includeItemsFromAllDrives: true,
      spaces: "drive",
    };

    if (q) {
      qParts.push(`name contains '${esc(q)}'`);
      listParams.corpora = "allDrives";
    } else {
      qParts.push(`'${esc(parentId)}' in parents`);
      listParams.corpora = "user";
    }
    listParams.q = qParts.join(" and ");
    if (pageToken) listParams.pageToken = pageToken;

    const { data: listData } = await drive.files.list(listParams);

    if (listData.files) {
      const pathPromises = listData.files.map((file) =>
        limit(() => getDisplayPath(drive, file))
      );
      const displayPaths = await Promise.all(pathPromises);

      (listData.files as any[]).forEach((file, index) => {
        file.displayPath = displayPaths[index];
      });
    }

    return NextResponse.json(listData);

  } catch (_e) {
    const err = _e as Error;
    console.error(`[Google Drive API] Error in /api/drive/folders: ${err.message}`, {
      stack: err.stack,
    });
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
