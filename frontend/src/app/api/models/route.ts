import { NextResponse } from "next/server";
import { readFile } from "fs/promises";
import path from "path";
import yaml from "js-yaml";

interface RawModel {
  id: string;
  label: string;
  input_cost?: number;
  output_cost?: number;
  [key: string]: unknown;
}

export async function GET() {
  const modelsPath = path.resolve(process.cwd(), "models.yaml");
  const file = await readFile(modelsPath, "utf8");
  const parsed = yaml.load(file);

  if (!Array.isArray(parsed)) {
    return NextResponse.json({ error: "models.yaml should contain a list" }, { status: 500 });
  }

  const models = (parsed as RawModel[]).map((model) => ({
    id: model.id,
    label: model.label,
    input_cost: model.input_cost ?? null,
    output_cost: model.output_cost ?? null,
  }));

  return NextResponse.json({ models });
}
