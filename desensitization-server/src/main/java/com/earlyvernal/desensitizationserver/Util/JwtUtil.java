package com.earlyvernal.desensitizationserver.Util;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

public class JwtUtil {

    private static final String SECRET = "dsh-desensitization-secret-key-2026-very-long-string";

    private static final long EXPIRE = 7L * 24 * 60 * 60 * 1000;

    private static final SecretKey KEY =
            Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8));

    public static String createToken(Long userId,String username){
        Map<String,Object> claims=new HashMap<>();
        claims.put("userId",userId);
        claims.put("username",username);

        return Jwts.builder()
                .setClaims(claims)
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis()+EXPIRE))
                .signWith(KEY, SignatureAlgorithm.HS256)
                .compact();
    }

    
}
