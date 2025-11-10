export interface Task {
  id: number,
  kind: string,
  role: string,
  owner_id: string,
  prompt: string,
  status: string,
  options: Option[],
  data?: NightDetails
}

export interface Option {
  id: string,
  name: string,
  role: Role
}

export interface Role {
  id: string,
  owner: string,
  name: string  
}

export interface NightDetails {
  night: number,
  wake_list: Role[]
}