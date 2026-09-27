import { api } from "./api";

export interface CreateAnalysisRequest {
  product_name: string;
  description: string;
  procurement_purpose?: string;
  intended_application?: string;
  material?: string;
  technical_specifications?: string;
  performance_requirements?: string;
  safety_requirements?: string;
  quantity?: number;
}

export interface Analysis {
  id: string;
  product_name: string;
  description: string;
  procurement_purpose?: string;
  intended_application?: string;
  material?: string;
  technical_specifications?: string;
  performance_requirements?: string;
  safety_requirements?: string;
  quantity?: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export async function createAnalysis(
  payload: CreateAnalysisRequest
): Promise<Analysis> {
  const response = await api.post<Analysis>(
    "/analyses",
    payload
  );

  return response.data;
}

export async function getAnalysis(
  id: string
): Promise<Analysis> {
  const response = await api.get<Analysis>(
    `/analyses/${id}`
  );

  return response.data;
}