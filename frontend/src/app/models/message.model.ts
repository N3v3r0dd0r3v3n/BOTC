export interface Task {
  id: number,
  kind: string,
  role: string,
  owner_id: string,
  prompt: string,
  status: string,
  options: Option[]
}

export interface Option {
  id: string,
  name: string
}