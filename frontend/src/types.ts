export interface VMNode {
    id: string;
    label: string;
    template_id: number;
    role: 'jumpbox_main' | 'jumpbox_local' | 'service';
}

export interface VMLink {
    source: string;
    target: string;
}

export interface CyberRangeRequest {
  range_metadata: {
    id: string;
    name: string;
  };
  nodes: VMNode[];
  links: VMLink[];
}