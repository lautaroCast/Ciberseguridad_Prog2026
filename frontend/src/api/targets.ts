import { request } from "./client";
import type { TargetCreate, TargetRead, TargetUpdate } from "../types";

export function listTargets(isActive?: boolean): Promise<TargetRead[]> {
  return request<TargetRead[]>("/targets", { query: { is_active: isActive } });
}

export function createTarget(body: TargetCreate): Promise<TargetRead> {
  return request<TargetRead>("/targets", { method: "POST", body });
}

export function getTarget(id: string): Promise<TargetRead> {
  return request<TargetRead>(`/targets/${id}`);
}

export function updateTarget(id: string, body: TargetUpdate): Promise<TargetRead> {
  return request<TargetRead>(`/targets/${id}`, { method: "PATCH", body });
}

export function deleteTarget(id: string): Promise<void> {
  return request<void>(`/targets/${id}`, { method: "DELETE" });
}
