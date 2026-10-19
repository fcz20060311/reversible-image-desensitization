package com.earlyvernal.desensitizationserver.DTO;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

@Data
public class PythonDesensitizeResp {

    private String key;

    private List<Img> images;

    @Data
    public static class Img{
        private String filename;

        @JsonProperty("region_count")
        private Integer regionCount;

        @JsonProperty("image_base64")
        private String imageBase64;

        @JsonProperty("annotated_base64")
        private String annotatedBase64;
    }
}
