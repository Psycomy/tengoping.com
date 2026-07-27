import authorsJson from './authors.json';

export interface AuthorSocial {
  github?: string;
  twitter?: string;
  linkedin?: string;
}

export interface Author {
  id: string;
  name: string;
  avatar: string;
  bio: string;
  bioShort: string;
  social: AuthorSocial;
}

// El JSON queda como fuente de datos editable; este módulo solo aporta el tipo
// (evita los casts de `social`, cuyo tipo inferido variaba por autor).
export const authors: Author[] = authorsJson;
