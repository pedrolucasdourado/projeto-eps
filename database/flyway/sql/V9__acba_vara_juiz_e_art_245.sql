-- V9: campos da vara/juiz competente e bloco do Art. 245 §§ 2º, 3º e 4º do CPP
-- (arrombamento, emprego de força e morador ausente) no auto.
--
-- Os três cenários são caixas de seleção independentes; cada um tem um campo
-- livre de observações para detalhamento.

ALTER TABLE acba_records
    ADD COLUMN nome_vara_criminal       VARCHAR(220) NOT NULL DEFAULT '',
    ADD COLUMN nome_juiz                VARCHAR(220) NOT NULL DEFAULT '',
    ADD COLUMN arrombamento_245_2       BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN arrombamento_245_2_obs   TEXT NOT NULL DEFAULT '',
    ADD COLUMN forca_coisas_245_3       BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN forca_coisas_245_3_obs   TEXT NOT NULL DEFAULT '',
    ADD COLUMN morador_ausente_245_4    BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN morador_ausente_245_4_obs TEXT NOT NULL DEFAULT '';
